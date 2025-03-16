import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# Параметри для підключення до PostgreSQL
DB_NAME = "postgres-todos"
DB_USER = "postgres"
DB_PASSWORD = "mydb111"
DB_HOST = "localhost"
DB_PORT = "5432"

# Функція для отримання з'єднання з БД
@contextmanager
def get_db():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True
    try:
        yield conn
    finally:
        conn.close()

# Функція для виконання SELECT одного запису
def fetch_one(query, params=None):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()  # Повертає один запис або None

# Функція для виконання SELECT багатьох записів
def fetch_all(query, params=None):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()  # Повертає список записів

# Функція для виконання INSERT, UPDATE, DELETE
def execute_query(query, params=None, fetch=True):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch:  # Якщо треба отримати результат
                return cur.fetchall()
            conn.commit()
