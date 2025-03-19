from bson import ObjectId
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Path, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from typing import List, Optional

from starlette import status
from pymongo import MongoClient
from starlette.responses import JSONResponse

from .auth import get_current_user, templates

# Підключення до MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['todo-app']
todos_collection = db['todos']
categories_collection = db['categories']
todo_category_collection = db['todo_category']

router = APIRouter(
    prefix="/todos",
    tags=["Todos"],
    responses={404: {"description": "Not found"}}
)

@router.get("/", response_class=HTMLResponse, summary="List all Todos")
async def read_all_by_user(
    request: Request,
    completed: Optional[str] = Query(None, description="Filter by completion status"),  # Changed to str to handle 'true'/'false' as string
    sort_by: Optional[str] = Query(None, description="Sort by field (priority or title)"),
    sort_order: Optional[int] = Query(1, description="Sort order: 1 (asc) or -1 (desc)")
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    filter_query = {"owner_id": user["id"]}
    print(completed)
    if completed and completed != "all":
        filter_query["complete"] = completed.lower() == 'true'

    todos = list(todos_collection.find(filter_query))

    for todo in todos:
        todo["categories"] = list(todo_category_collection.find({"todo_id": todo["_id"]}))
        todo["id"] = str(todo["_id"])

    if sort_by:
        todos.sort(key=lambda x: x.get(sort_by, ""), reverse=(sort_order == -1))

    return templates.TemplateResponse("home.html", {
        "request": request, "todos": todos, "user": user, "completed": completed
    })


@router.get("/add-todo", response_class=HTMLResponse, summary="Display Add Todo Form")
async def add_new_todo(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth")

    categories = list(categories_collection.find())
    return templates.TemplateResponse("add-todo.html", {"request": request, "user": user, "categories": categories})


@router.post("/add-todo", response_class=HTMLResponse, summary="Create a new Todo")
async def create_todo(
        request: Request,
        title: str = Form(...),
        description: str = Form(...),
        priority: int = Form(...),
        category_ids: List[str] = Form([]),  # Змінено на List[str]
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=303)

    # Конвертація рядкових значень у ObjectId
    category_object_ids = [ObjectId(cid) for cid in category_ids if cid]

    new_todo = {
        "title": title,
        "description": description,
        "priority": priority,
        "complete": False,
        "owner_id": user["id"],
        "categories": category_object_ids,  # Зберігаємо як список ObjectId
    }

    print(new_todo)
    todo_result = todos_collection.insert_one(new_todo)
    todo_id = todo_result.inserted_id

    return RedirectResponse(url="/todos", status_code=303)


@router.get("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: str):
    print(f"Received request for editing todo with id: {todo_id}")

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    try:
        todo_object_id = ObjectId(todo_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid todo ID format")

    todo = todos_collection.find_one({"_id": todo_object_id, "owner_id": user["id"]})
    todo["id"] = str(todo["_id"])
    print(todo)
    if not todo:
        print(f"Todo with id {todo_id} not found for user {user['id']}")
        return RedirectResponse(url="/todos", status_code=status.HTTP_404_NOT_FOUND)

    categories = list(categories_collection.find())
    selected_categories = todo.get("categories", [])  # Fetch directly from todo

    return templates.TemplateResponse("edit-todo.html", {
        "request": request,
        "todo": todo,
        "user": user,
        "categories": categories,
        "selected_categories": selected_categories
    })

@router.put("/edit-todo/{todo_id}")
async def update_todo(
        request: Request,
        todo_id: str,
        title: str = Form(...),
        description: str = Form(...),
        priority: int = Form(...),
        category_ids: List[str] = Form([]),  # Приймаємо категорії як список рядків (ID)
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=302)

    try:
        todo_object_id = ObjectId(todo_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid todo ID format")

    # Перевіряємо, чи існує задача в базі даних
    todo = todos_collection.find_one({"_id": todo_object_id, "owner_id": user["id"]})
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    # Конвертуємо рядки в ObjectId для MongoDB
    category_object_ids = [ObjectId(cat_id) for cat_id in category_ids if ObjectId.is_valid(cat_id)]

    # Оновлення задачі
    try:
        todos_collection.update_one(
            {"_id": todo_object_id},
            {"$set": {
                "title": title,
                "description": description,
                "priority": priority,
                "categories": category_object_ids  # Оновлюємо категорії як ObjectId
            }}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error updating todo: " + str(e))

    return {"message": "Todo updated successfully"}
@router.patch("/complete/{todo_id}", response_class=JSONResponse)
async def complete_todo(request: Request, todo_id: str):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth")
    print(todo_id)
    try:
        todo_object_id = ObjectId(todo_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid todo ID format")

    todo = todos_collection.find_one({"_id": todo_object_id, "owner_id": user.get("id")})
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    complete_status = not todo["complete"]
    todos_collection.update_one({"_id": todo_object_id}, {"$set": {"complete": complete_status}})

    return JSONResponse(content={"message": "Todo updated successfully"})


@router.delete("/delete/{todo_id}")
async def delete_todo(request: Request, todo_id: str):
    user = await get_current_user(request)
    if user is None:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})

    try:
        todo_object_id = ObjectId(todo_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid todo ID format")

    todos_collection.delete_one({"_id": todo_object_id, "owner_id": user.get("id")})

    return JSONResponse(status_code=200, content={"message": "Todo deleted successfully"})