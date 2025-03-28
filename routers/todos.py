import sys
from http.client import HTTPException
from fastapi import Query
from typing import List, Optional
from pydantic import BaseModel
sys.path.append("..")
from starlette import status
from starlette.responses import RedirectResponse
from fastapi import Depends, APIRouter, Request, Form, Path
import models
from database import engine, get_db
from sqlalchemy.orm import Session
from .auth import get_current_user
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/todos",
    tags=["Todos"],
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse, summary="List all Todos")
async def read_all_by_user(
        request: Request,
        db: Session = Depends(get_db),
        completed: Optional[str] = Query(None),  # Simple query parameter, no description
        sort_by: Optional[str] = Query(None),
        sort_order: Optional[int] = Query(1)
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    query = db.query(models.Todos).filter(models.Todos.owner_id == user.get("id"))

    # Apply filtering if completed is provided
    if completed and completed != "all":
        completed_value = completed.lower() == 'true'
        query = query.filter(models.Todos.complete == completed_value)

    # Apply sorting if required
    if sort_by:
        if sort_order == 1:
            query = query.order_by(getattr(models.Todos, sort_by).asc())
        elif sort_order == -1:
            query = query.order_by(getattr(models.Todos, sort_by).desc())

    # Fetch the results
    todos = query.all()

    return templates.TemplateResponse("home.html", {"request": request, "todos": todos, "user": user, "completed": completed})

@router.get("/add-todo", response_class=HTMLResponse, summary="Display Add Todo Form", description="Renders a form to create a new todo item.")
async def add_new_todo(request: Request, db: Session = Depends(get_db)):
    """
    Displays a form where users can add new todos.
    - **Returns**: Rendered HTML page with form.
    """
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    categories = db.query(models.Category).all()
    return templates.TemplateResponse("add-todo.html", {"request": request, "user": user, "categories": categories})


@router.patch("/complete/{todo_id}", response_class=HTMLResponse)
async def complete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    todo.complete = not todo.complete

    db.add(todo)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.post("/add-todo", response_class=HTMLResponse, summary="Create a new Todo", description="Processes form data and creates a new todo item.")
async def create_todo(
    request: Request,
    title: str = Form(..., description="Title of the todo"),
    description: str = Form(..., description="Detailed description"),
    priority: int = Form(..., description="Priority level"),
    category_ids: List[int] = Form([], description="List of category IDs"),
    db: Session = Depends(get_db)
):
    """
    Creates a new todo item based on user input.
    - **Returns**: Redirects to the todos list.
    """
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo_model = models.Todos(
        title=title, description=description, priority=priority, complete=False, owner_id=user.get("id")
    )
    for cat_id in category_ids:
        category = db.query(models.Category).filter(models.Category.id == cat_id).first()
        if category:
            todo_model.categories.append(category)
    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/edit-todo/{todo_id}", response_class=HTMLResponse, summary="Edit a Todo", description="Displays a form to edit an existing todo item.")
async def edit_todo(request: Request, todo_id: int = Path(..., description="ID of the todo to edit"), db: Session = Depends(get_db)):
    """
    Fetches a todo item for editing.
    - **Returns**: Rendered HTML form.
    """
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if not todo:
        return RedirectResponse(url="/todos", status_code=status.HTTP_404_NOT_FOUND)
    categories = db.query(models.Category).all()
    selected_categories = [tc.id for tc in todo.categories] if todo.categories else []
    return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user, "categories": categories, "selected_categories": selected_categories})


class TodoUpdate(BaseModel):
    title: str
    description: str
    priority: int
    category_ids: List[int]

@router.put("/edit-todo/{todo_id}")
async def update_todo(
    todo_id: int,
    todo_data: TodoUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates a specific todo item including categories.
    """
    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    todo.title = todo_data.title
    todo.description = todo_data.description
    todo.priority = todo_data.priority

    # Update categories
    todo.categories = db.query(models.Category).filter(models.Category.id.in_(todo_data.category_ids)).all()

    db.commit()

    return {"message": "Todo updated successfully"}


@router.delete("/delete/{todo_id}", summary="Delete a Todo", description="Deletes a todo item by ID.")
async def delete_todo(request: Request, todo_id: int = Path(..., description="ID of the todo to delete"), db: Session = Depends(get_db)):
    """
    Deletes a todo item belonging to the authenticated user.
    - **Returns**: Redirects to the todos list.
    """
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id, models.Todos.owner_id == user.get("id")).first()
    if todo_model is None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
    db.query(models.Todos).filter(models.Todos.id == todo_id, models.Todos.owner_id == user.get("id")).delete()
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)