import sys

sys.path.append("..")

from starlette.responses import RedirectResponse
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Form
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7"
ALGORITHM = "HS256"

templates = Jinja2Templates(directory="templates")

# Підключення до MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['todo-app']
users_collection = db['users']

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"user": "Not authorized"}}
)


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("email")
        self.password = form.get("password")


def get_password_hash(password):
    return bcrypt_context.hash(password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str):
    user = users_collection.find_one({"username": username})
    if not user or not verify_password(password, user['hashed_password']):
        return None
    return user


def create_access_token(username: str, user_id: str, role: str,
                        expires_delta: Optional[timedelta] = None):
    encode = {"sub": username, "id": user_id, "role": role}
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")
        if username is None or user_id is None:
            logout(request)
        return {"username": username, "id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=404, detail="Not found")

@router.post("/token", response_model=Token)
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(user['username'], str(user['_id']), user['role'], expires_delta=timedelta(minutes=60))
    response.set_cookie(key="access_token", value=token, httponly=True)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return RedirectResponse(url="/auth")


@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, email: str = Form(...), username: str = Form(...),
                        firstname: str = Form(...), lastname: str = Form(...),
                        password: str = Form(...), password2: str = Form(...)):
    if password != password2:
        return templates.TemplateResponse("register.html", {"request": request, "msg": "Passwords do not match"})

    # Перевірка на існування користувача
    existing_user = users_collection.find_one({"$or": [{"username": username}, {"email": email}]})
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": request, "msg": "Username or email already taken"})

    hashed_password = get_password_hash(password)

    # Додавання користувача до MongoDB
    users_collection.insert_one({
        "username": username,
        "email": email,
        "first_name": firstname,
        "last_name": lastname,
        "hashed_password": hashed_password,
        "is_active": True,
        "role": "user"
    })

    return templates.TemplateResponse("login.html", {"request": request, "msg": "User successfully created"})


@router.get("/", response_class=HTMLResponse)
async def authentication_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/", response_class=HTMLResponse)
async def login(request: Request):
    form = LoginForm(request)
    await form.create_oauth_form()
    response = RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
    user = authenticate_user(form.username, form.password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "msg": "Incorrect Username or Password"})
    token = create_access_token(user['username'], str(user['_id']), user['role'], expires_delta=timedelta(minutes=60))
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response
