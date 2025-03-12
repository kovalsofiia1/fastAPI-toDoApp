import sys
from http.client import HTTPException
from typing import List

sys.path.append("..")

from starlette import status
from starlette.responses import RedirectResponse

from fastapi import Depends, APIRouter, Request, Form
import models
from database import engine, get_db
from sqlalchemy.orm import Session
from .auth import get_current_user

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix="/todos",
    tags=["todos"],
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def read_all_by_user(request: Request, db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todos = db.query(models.Todos).filter(models.Todos.owner_id == user.get("id")).all()

    return templates.TemplateResponse("home.html", {"request": request, "todos": todos, "user": user})


@router.get("/add-todo", response_class=HTMLResponse)
async def add_new_todo(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    categories = db.query(models.Category).all()
    return templates.TemplateResponse("add-todo.html", {"request": request, "user": user, "categories": categories})


@router.post("/add-todo", response_class=HTMLResponse)
async def create_todo(request: Request, title: str = Form(...), description: str = Form(...),
                      priority: int = Form(...), category_ids: List[int] = Form([]), db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = models.Todos(
        title=title,
        description=description,
        priority=priority,
        complete=False,
        owner_id=user.get("id")
    )

    for cat_id in category_ids:
        category = db.query(models.Category).filter(models.Category.id == cat_id).first()
        if category:
            todo_model.categories.append(category)  # Add Category directly to the relationship

    db.add(todo_model)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


# @router.get("/edit-todo/{todo_id}", response_class=HTMLResponse)
# async def edit_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
#
#     user = await get_current_user(request)
#     if user is None:
#         return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
#
#     todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
#     categories = db.query(models.Category).all()
#     selected_categories = [tc.id for tc in todo.categories]
#
#     return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user, "categories": categories, "selected_categories": selected_categories})

@router.get("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    print(f"Searching for todo_id: {todo_id}")
    if not todo:
        return RedirectResponse(url="/todos", status_code=status.HTTP_404_NOT_FOUND)


    categories = db.query(models.Category).all()
    selected_categories = [tc.id for tc in todo.categories] if todo.categories else []

    return templates.TemplateResponse(
        "edit-todo.html",
        {"request": request, "todo": todo, "user": user, "categories": categories, "selected_categories": selected_categories}
    )

@router.post("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def update_todo(
    request: Request,
    todo_id: int,
    title: str = Form(...),
    description: str = Form(...),
    priority: int = Form(...),
    category_ids: List[int] = Form([]),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    todo.title = title
    todo.description = description
    todo.priority = priority
    todo.categories = db.query(models.Category).filter(models.Category.id.in_(category_ids)).all()

    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/delete/{todo_id}")
async def delete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id)\
        .filter(models.Todos.owner_id == user.get("id")).first()

    if todo_model is None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

    db.query(models.Todos).filter(models.Todos.id == todo_id).delete()

    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get("/complete/{todo_id}", response_class=HTMLResponse)
async def complete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    todo.complete = not todo.complete

    db.add(todo)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
