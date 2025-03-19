from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId

# Модель користувача
class User(BaseModel):
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    role: str = "user"

    class Config:
        json_encoders = {
            ObjectId: str  # Перетворюємо ObjectId в строку для серіалізації
        }

# Модель задачі
class Todo(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int
    complete: bool = False
    owner_id: str  # це буде ID користувача
    categories: List[str] = []  # список категорій

    class Config:
        json_encoders = {
            ObjectId: str
        }

# Модель категорії
class Category(BaseModel):
    name: str
    description: Optional[str] = None

    class Config:
        json_encoders = {
            ObjectId: str
        }
