from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import execute_query, fetch_one, fetch_all
from routers.auth import get_current_user

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
    categories = fetch_all("SELECT * FROM categories")
    return templates.TemplateResponse("categories.html", {"request": request, "categories": categories, "user": user})

@router.get("/create", response_class=HTMLResponse)
async def create_category_form(request: Request, user: dict = Depends(get_current_user)):
    admin_required(user)
    return templates.TemplateResponse("category_form.html", {"request": request, "user": user, "action": "Create"})

@router.post("/create", response_class=HTMLResponse)
async def create_category(request: Request, name: str = Form(...), description: str = Form(...), user: dict = Depends(get_current_user)):
    admin_required(user)
    existing_category = fetch_one("SELECT * FROM categories WHERE name = %s", (name,))
    if existing_category:
        return templates.TemplateResponse("category_form.html", {"request": request, "msg": "Category already exists", "user": user, "action": "Create"})
    execute_query("INSERT INTO categories (name, description) VALUES (%s, %s)", (name, description), fetch=False)
    return RedirectResponse(url="/categories", status_code=303)

@router.get("/edit/{category_id}", response_class=HTMLResponse)
async def edit_category_form(request: Request, category_id: int, user: dict = Depends(get_current_user)):
    admin_required(user)
    category = fetch_one("SELECT * FROM categories WHERE id = %s", (category_id,))
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return templates.TemplateResponse("category_form.html", {"request": request, "category": category, "user": user, "action": "Edit"})

@router.post("/edit/{category_id}", response_class=HTMLResponse)
async def update_category(request: Request, category_id: int, name: str = Form(...), description: str = Form(...), user: dict = Depends(get_current_user)):
    admin_required(user)
    category = fetch_one("SELECT * FROM categories WHERE id = %s", (category_id,))
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    execute_query("UPDATE categories SET name = %s, description = %s WHERE id = %s", (name, description, category_id), fetch=False)
    return RedirectResponse(url="/categories", status_code=303)

@router.get("/delete/{category_id}", response_class=HTMLResponse)
async def delete_category(category_id: int, user: dict = Depends(get_current_user)):
    admin_required(user)
    category = fetch_one("SELECT * FROM categories WHERE id = %s", (category_id,))
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    execute_query("DELETE FROM categories WHERE id = %s", (category_id,), fetch=False)
    return RedirectResponse(url="/categories", status_code=303)
