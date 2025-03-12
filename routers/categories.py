from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from database import get_db
from models import Category
from routers.auth import get_current_user  # Import authentication function
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/categories",
    tags=["categories"]
)

templates = Jinja2Templates(directory="templates")


# Middleware to ensure only admins access category management pages
def admin_required(user=Depends(get_current_user)):
    if user is None or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied. Admins only.")


# Display all categories
@router.get("/", response_class=HTMLResponse)
async def get_categories(request: Request, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    admin_required(user)
    categories = db.query(Category).all()
    return templates.TemplateResponse("categories.html", {"request": request, "categories": categories, "user": user})


# Show category creation form
@router.get("/create", response_class=HTMLResponse)
async def create_category_form(request: Request, user: dict = Depends(get_current_user)):
    admin_required(user)
    return templates.TemplateResponse("category_form.html", {"request": request, "user": user, "action": "Create"})


# Process category creation
@router.post("/create", response_class=HTMLResponse)
async def create_category(
        request: Request,
        name: str = Form(...),
        description: str = Form(...),
        db: Session = Depends(get_db),
        user: dict = Depends(get_current_user),
):
    admin_required(user)

    if db.query(Category).filter(Category.name == name).first():
        return templates.TemplateResponse("category_form.html",
                                          {"request": request, "msg": "Category already exists", "user": user,
                                           "action": "Create"})

    new_category = Category(name=name, description=description)
    db.add(new_category)
    db.commit()

    return RedirectResponse(url="/categories", status_code=303)


# Show category update form
@router.get("/edit/{category_id}", response_class=HTMLResponse)
async def edit_category_form(request: Request, category_id: int, db: Session = Depends(get_db),
                             user: dict = Depends(get_current_user)):
    admin_required(user)
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    return templates.TemplateResponse("category_form.html",
                                      {"request": request, "category": category, "user": user, "action": "Edit"})


# Process category update
@router.post("/edit/{category_id}", response_class=HTMLResponse)
async def update_category(
        request: Request,
        category_id: int,
        name: str = Form(...),
        description: str = Form(...),
        db: Session = Depends(get_db),
        user: dict = Depends(get_current_user),
):
    admin_required(user)
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    category.name = name
    category.description = description
    db.commit()

    return RedirectResponse(url="/categories", status_code=303)


# Delete a category
@router.get("/delete/{category_id}", response_class=HTMLResponse)
async def delete_category(category_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    admin_required(user)
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()

    return RedirectResponse(url="/categories", status_code=303)
