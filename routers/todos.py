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
        categories = execute_query(query, (todo["id"],), fetch=True)
        todo["categories"] = [{"id": c[0], "name": c[1]} for c in categories]

    if todos is None:
        todos = []

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
    return templates.TemplateResponse("add-todo.html", {"request": request, "user": user, "categories": [{"id": c[0], "name": c[1]} for c in categories]})

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
    if todo_id:  # Переконуємось, що значення не пусте
        todo_id = todo_id[0][0]  # Витягуємо ідентифікатор (id)

    for cat_id in category_ids:
        query = "INSERT INTO todo_category (todo_id, category_id) VALUES (%s, %s);"
        execute_query(query, (todo_id, cat_id), fetch=False)

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
    """
    categories = execute_query(query, (todo_id,))

    if categories:
        todo["categories"] = [{"id": c[0], "name": c[1]} for c in categories]

    selected_categories = [c["id"] for c in todo["categories"]]

    print({
            "request": request,
            "todo": todo,
            "user": user,
            "categories": todo["categories"],
            "selected_categories": selected_categories
        })
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
