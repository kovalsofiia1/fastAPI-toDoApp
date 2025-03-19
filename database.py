
from pymongo import MongoClient
from pymongo.database import Database

# Створюємо з'єднання з MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Вибір бази даних
db: Database = client['todo-app']

collections = db.list_collection_names()
print(f"Колекції в базі даних 'todo-app': {collections}")