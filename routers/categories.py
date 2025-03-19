from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from starlette.responses import JSONResponse

from routers.auth import get_current_user

# Підключення до MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['todo-app']
categories_collection = db['categories']

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)

templates = Jinja2Templates(directory="templates")


def admin_required(user=Depends(get_current_user)):
    if user is None or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied. Admins only.")


@router.get("/", response_class=HTMLResponse)
async def get_categories(request: Request, user: dict = Depends(get_current_user)):
    admin_required(user)
    categories = list(categories_collection.find())
    for category in categories:
        category["id"] = str(category["_id"])
    return templates.TemplateResponse("categories.html", {"request": request, "categories": categories, "user": user})


@router.get("/create", response_class=HTMLResponse)
async def create_category_form(request: Request, user: dict = Depends(get_current_user)):
    admin_required(user)
    return templates.TemplateResponse("category_form.html", {"request": request, "user": user, "action": "Create"})


@router.post("/create", response_class=HTMLResponse)
async def create_category(request: Request, name: str = Form(...), description: str = Form(...),
                          user: dict = Depends(get_current_user)):
    admin_required(user)
    existing_category = categories_collection.find_one({"name": name})
    if existing_category:
        return templates.TemplateResponse("category_form.html",
                                          {"request": request, "msg": "Category already exists", "user": user,
                                           "action": "Create"})

    categories_collection.insert_one({"name": name, "description": description})
    return RedirectResponse(url="/categories", status_code=303)


@router.get("/edit/{category_id}", response_class=HTMLResponse)
async def edit_category_form(request: Request, category_id: str, user: dict = Depends(get_current_user)):
    admin_required(user)
    try:
        category_object_id = ObjectId(category_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid todo ID format")

    category = categories_collection.find_one({"_id": category_object_id})
    category["id"] = str(category["_id"])

    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return templates.TemplateResponse("category_form.html",
                                      {"request": request, "category": category, "user": user, "action": "Edit"})


@router.post("/edit/{category_id}", response_class=HTMLResponse)
async def update_category(request: Request, category_id: str, name: str = Form(...), description: str = Form(...),
                          user: dict = Depends(get_current_user)):
    admin_required(user)

    try:
        category_object_id = ObjectId(category_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid todo ID format")


    category = categories_collection.find_one({"_id": category_object_id})
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    categories_collection.update_one({"_id": category_object_id}, {"$set": {"name": name, "description": description}})
    return RedirectResponse(url="/categories", status_code=303)


@router.delete("/delete/{category_id}")
async def delete_category(request: Request, category_id: str, user: dict = Depends(get_current_user)):
    admin_required(user)
    if user is None:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})

    try:
        category_object_id = ObjectId(category_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid todo ID format")

    category = categories_collection.find_one({"_id": category_object_id})

    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    categories_collection.delete_one({"_id": category_object_id})
    return JSONResponse(status_code=200, content={"message": "Category deleted successfully"})
