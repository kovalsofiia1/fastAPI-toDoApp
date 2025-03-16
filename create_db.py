import psycopg2
from psycopg2 import sql

# Параметри для підключення до PostgreSQL
DB_NAME = "postgres"  # Це ім'я бази даних, до якої ти підключатимешся для створення нової БД
DB_USER = "postgres"
DB_PASSWORD = "mydb111"
DB_HOST = "localhost"
DB_PORT = "5432"
CREATED_DB_NAME = "postgres-todos"

# Функція для підключення до PostgreSQL
def get_connection(dbname=DB_NAME):
    return psycopg2.connect(
        dbname=dbname,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

# Створення бази даних
def create_database():
    connection = get_connection(dbname="postgres")
    connection.autocommit = True  # Вимикаємо автоматичні транзакції для цієї операції
    cursor = connection.cursor()
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(CREATED_DB_NAME)))
    connection.commit()
    cursor.close()
    connection.close()
    print(f"Database {CREATED_DB_NAME} has been created successfully.")

create_database()  # Викликаємо функцію для створення бази даних
