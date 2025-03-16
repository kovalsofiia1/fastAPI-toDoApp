# import sys
# from http.client import HTTPException
# from typing import List
# from pydantic import BaseModel
# sys.path.append("..")
# from starlette import status
# from starlette.responses import RedirectResponse
# from fastapi import Depends, APIRouter, Request, Form, Path
# import models
# from database import engine, get_db
# from sqlalchemy.orm import Session
# from .auth import get_current_user
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
#
# router = APIRouter(
#     prefix="/todos",
#     tags=["Todos"],
#     responses={404: {"description": "Not found"}}
# )
#
# models.Base.metadata.create_all(bind=engine)
# templates = Jinja2Templates(directory="templates")
#
# @router.get("/", response_class=HTMLResponse, summary="List all Todos", description="Fetch all todo items belonging to the current user.")
# async def read_all_by_user(request: Request, db: Session = Depends(get_db)):
#     """
#     Retrieves all todo items belonging to the authenticated user.
#     - **Returns**: Rendered HTML page with user's todos.
#     """
#     user = await get_current_user(request)
#     if user is None:
#         return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
#     todos = db.query(models.Todos).filter(models.Todos.owner_id == user.get("id")).all()
#     return templates.TemplateResponse("home.html", {"request": request, "todos": todos, "user": user})
#
# @router.get("/add-todo", response_class=HTMLResponse, summary="Display Add Todo Form", description="Renders a form to create a new todo item.")
# async def add_new_todo(request: Request, db: Session = Depends(get_db)):
#     """
#     Displays a form where users can add new todos.
#     - **Returns**: Rendered HTML page with form.
#     """
#     user = await get_current_user(request)
#     if user is None:
#         return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
#     categories = db.query(models.Category).all()
#     return templates.TemplateResponse("add-todo.html", {"request": request, "user": user, "categories": categories})
#
#
# @router.patch("/complete/{todo_id}", response_class=HTMLResponse)
# async def complete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
#     user = await get_current_user(request)
#     if user is None:
#         return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
#
#     todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
#
#     todo.complete = not todo.complete
#
#     db.add(todo)
#     db.commit()
#
#     return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
#
# @router.post("/add-todo", response_class=HTMLResponse, summary="Create a new Todo", description="Processes form data and creates a new todo item.")
# async def create_todo(
#     request: Request,
#     title: str = Form(..., description="Title of the todo"),
#     description: str = Form(..., description="Detailed description"),
#     priority: int = Form(..., description="Priority level"),
#     category_ids: List[int] = Form([], description="List of category IDs"),
#     db: Session = Depends(get_db)
# ):
#     """
#     Creates a new todo item based on user input.
#     - **Returns**: Redirects to the todos list.
#     """
#     user = await get_current_user(request)
#     if user is None:
#         return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
#     todo_model = models.Todos(
#         title=title, description=description, priority=priority, complete=False, owner_id=user.get("id")
#     )
#     for cat_id in category_ids:
#         category = db.query(models.Category).filter(models.Category.id == cat_id).first()
#         if category:
#             todo_model.categories.append(category)
#     db.add(todo_model)
#     db.commit()
#     return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
#
# @router.get("/edit-todo/{todo_id}", response_class=HTMLResponse, summary="Edit a Todo", description="Displays a form to edit an existing todo item.")
# async def edit_todo(request: Request, todo_id: int = Path(..., description="ID of the todo to edit"), db: Session = Depends(get_db)):
#     """
#     Fetches a todo item for editing.
#     - **Returns**: Rendered HTML form.
#     """
#     user = await get_current_user(request)
#     if user is None:
#         return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
#     todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
#     if not todo:
#         return RedirectResponse(url="/todos", status_code=status.HTTP_404_NOT_FOUND)
#     categories = db.query(models.Category).all()
#     selected_categories = [tc.id for tc in todo.categories] if todo.categories else []
#     return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user, "categories": categories, "selected_categories": selected_categories})
#
#
# class TodoUpdate(BaseModel):
#     title: str
#     description: str
#     priority: int
#     category_ids: List[int]
#
# @router.put("/edit-todo/{todo_id}")
# async def update_todo(
#     todo_id: int,
#     todo_data: TodoUpdate,
#     db: Session = Depends(get_db)
# ):
#     """
#     Updates a specific todo item including categories.
#     """
#     todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
#     if not todo:
#         raise HTTPException(status_code=404, detail="Todo not found")
#
#     todo.title = todo_data.title
#     todo.description = todo_data.description
#     todo.priority = todo_data.priority
#
#     # Update categories
#     todo.categories = db.query(models.Category).filter(models.Category.id.in_(todo_data.category_ids)).all()
#
#     db.commit()
#
#     return {"message": "Todo updated successfully"}
#
#
# @router.delete("/delete/{todo_id}", summary="Delete a Todo", description="Deletes a todo item by ID.")
# async def delete_todo(request: Request, todo_id: int = Path(..., description="ID of the todo to delete"), db: Session = Depends(get_db)):
#     """
#     Deletes a todo item belonging to the authenticated user.
#     - **Returns**: Redirects to the todos list.
#     """
#     user = await get_current_user(request)
#     if user is None:
#         return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
#     todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id, models.Todos.owner_id == user.get("id")).first()
#     if todo_model is None:
#         return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
#     db.query(models.Todos).filter(models.Todos.id == todo_id, models.Todos.owner_id == user.get("id")).delete()
#     db.commit()
#     return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
#



from fastapi import APIRouter, Request, Depends, HTTPException, Form, Path, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from typing import List

from starlette import status

from database import execute_query
from .auth import get_current_user, templates

router = APIRouter(
    prefix="/todos",
    tags=["Todos"],
    responses={404: {"description": "Not found"}}
)

@router.get("/", response_class=HTMLResponse, summary="List all Todos")
async def read_all_by_user(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    query = "SELECT * FROM todos WHERE owner_id = %s ORDER BY id;"
    # todos = execute_query(query, (user["id"],))
    todos = [
        {
            "id": t[0],
            "title": t[1],
            "description": t[2],
            "priority": t[3],
            "complete": t[4],
            "owner_id": t[5],
            "categories": []  # Пізніше сюди додамо категорії
        }
        for t in execute_query(query, (user["id"],), fetch=True)
    ]
    for todo in todos:
        query = """
        SELECT c.id, c.name FROM categories c
        JOIN todo_category tc ON c.id = tc.category_id
        WHERE tc.todo_id = %s;
        """
        todo["categories"] = execute_query(query, (todo["id"],), fetch=True)

    print(query)
    print("Fetched Todos:", todos)  # Додай це
    if todos is None:
        todos = []
    print("Fetched Todos:", todos)  # Додай це
    return templates.TemplateResponse("home.html", {"request": request, "todos": todos, "user": user})

@router.get("/add-todo", response_class=HTMLResponse, summary="Display Add Todo Form")
async def add_new_todo(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth")

    query = "SELECT * FROM categories"
    categories = execute_query(query)
    if categories is None:
        categories = []
    return templates.TemplateResponse("add-todo.html", {"request": request, "user": user, "categories": categories})

@router.post("/add-todo", response_class=HTMLResponse, summary="Create a new Todo")
async def create_todo(
        request: Request,
        title: str = Form(...),
        description: str = Form(...),
        priority: int = Form(...),
        category_ids: List[int] = Form([]),
    # user: dict = Depends(get_current_user)
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=303)

    query = """
    INSERT INTO todos (title, description, priority, complete, owner_id)
    VALUES (%s, %s, %s, %s, %s) RETURNING id;
    """
    todo_id = execute_query(query, (title, description, priority, False, user["id"]))

    for cat_id in category_ids:
        query = "INSERT INTO todo_category (todo_id, category_id) VALUES (%s, %s);"
        execute_query(query, (todo_id, cat_id))

    return RedirectResponse(url="/todos", status_code=303)

@router.get("/edit-todo/{todo_id}", response_class=HTMLResponse, summary="Edit a Todo", description="Displays a form to edit an existing todo item.")
async def edit_todo(request: Request, todo_id: int = Path(..., description="ID of the todo to edit")):
    """
    Fetches a todo item for editing.
    - **Returns**: Rendered HTML form.
    """
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    query = """
        SELECT id, title, description, priority, complete, owner_id 
        FROM todos WHERE id = %s AND owner_id = %s
    """
    result = execute_query(query, (todo_id, user["id"]))

    if not result:
        return RedirectResponse(url="/todos", status_code=status.HTTP_404_NOT_FOUND)

    todo = {
        "id": result[0][0],
        "title": result[0][1],
        "description": result[0][2],
        "priority": result[0][3],
        "complete": result[0][4],
        "owner_id": result[0][5],
        "categories": []  # Додамо категорії пізніше
    }

    # Отримуємо категорії, пов'язані з цим todo
    query = """
        SELECT c.id, c.name FROM categories c
        JOIN todo_category tc ON c.id = tc.category_id
        WHERE tc.todo_id = %s;
    """
    categories = execute_query(query, (todo_id,))

    if categories:
        todo["categories"] = [{"id": c[0], "name": c[1]} for c in categories]

    selected_categories = [c["id"] for c in todo["categories"]]

    return templates.TemplateResponse("edit-todo.html", {
        "request": request,
        "todo": todo,
        "user": user,
        "categories": todo["categories"],
        "selected_categories": selected_categories
    })


@router.put("/edit-todo/{todo_id}")
async def update_todo(
request: Request,
        todo_id: int,
        title: str = Form(...),
        description: str = Form(...),
        priority: int = Form(...),
        category_ids: List[int] = Form([]),  # Приймаємо список ID


):
    """
    Updates a specific todo item including categories.
    """
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=302)

    # Перевіряємо, чи існує todo
    query = "SELECT id FROM todos WHERE id = %s AND owner_id = %s;"
    result = execute_query(query, (todo_id, user["id"]))

    if not result:
        raise HTTPException(status_code=404, detail="Todo not found")

    # Оновлюємо основні дані todo
    query = """
        UPDATE todos 
        SET title = %s, description = %s, priority = %s 
        WHERE id = %s;
    """
    execute_query(query, (title, description, priority, todo_id), fetch=False)

    # Очищуємо старі категорії
    query = "DELETE FROM todo_category WHERE todo_id = %s;"
    execute_query(query, (todo_id,), fetch=False)

    # Додаємо нові категорії
    for cat_id in category_ids:
        query = "INSERT INTO todo_category (todo_id, category_id) VALUES (%s, %s);"
        execute_query(query, (todo_id, cat_id), fetch=False)

    return {"message": "Todo updated successfully"}

@router.patch("/complete/{todo_id}", response_class=HTMLResponse)
async def complete_todo(request: Request, todo_id: int
                        # , user: dict = Depends(get_current_user)
                        ):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth")

    query = "SELECT complete FROM todos WHERE id = %s AND owner_id = %s"
    todo = execute_query(query, (todo_id, user.get("id")))
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    complete_status = not todo[0][0]
    query = "UPDATE todos SET complete = %s WHERE id = %s"
    execute_query(query, (complete_status, todo_id), fetch=False)

    return RedirectResponse(url="/todos")

@router.delete("/delete/{todo_id}", response_class=HTMLResponse)
async def delete_todo(request: Request, todo_id: int
                      # , user: dict = Depends(get_current_user)
                      ):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth")

    query = "DELETE FROM todos WHERE id = %s AND owner_id = %s"
    execute_query(query, (todo_id, user.get("id")), fetch=False)

    return RedirectResponse(url="/todos")
