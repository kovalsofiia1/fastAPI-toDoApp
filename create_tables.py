from database import execute_query


def create_tables():
    create_tables_query = """
    -- Створення таблиці users
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        username VARCHAR(255) UNIQUE NOT NULL,
        first_name VARCHAR(255),
        last_name VARCHAR(255),
        hashed_password VARCHAR(255) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        role VARCHAR(50) DEFAULT 'user'
    );

    -- Створення таблиці todos
    CREATE TABLE IF NOT EXISTS todos (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        priority INTEGER NOT NULL,
        complete BOOLEAN DEFAULT FALSE,
        owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE
    );

    -- Створення таблиці categories
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        description TEXT
    );

    -- Створення зв'язуючої таблиці для many-to-many зв'язку між todos і categories
    CREATE TABLE IF NOT EXISTS todo_category (
        todo_id INTEGER REFERENCES todos(id) ON DELETE CASCADE,
        category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
        PRIMARY KEY (todo_id, category_id)
    );
    """

    # Виконання запиту для створення таблиць
    execute_query(create_tables_query)
    print("Таблиці були успішно створені!")


# Викликаємо функцію для створення таблиць
create_tables()
