# Authentication API

This is an authentication API built with FastAPI, SQLAlchemy, and JWT authentication.

## Features
- User registration and login
- Password hashing using bcrypt
- JWT-based authentication with access tokens
- Login sessions managed via cookies
- User logout functionality
- HTML-based login and registration pages
- Todo management with CRUD functionality
- Category management (admin-only access)

## Installation

1. Clone the repository:
   ```sh
   git clone git@github.com:kovalsofiia1/fastAPI-toDoApp.git
   cd fastAPI-toDoApp
   ```
2. Create a virtual environment and activate it:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Running the Application

```sh
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000/`

## API Endpoints

### Authentication
- `POST /auth/token` - User login (returns JWT token)
- `GET /auth/logout` - User logout
- `GET /auth/` - Login page (HTML)
- `POST /auth/` - Authenticate and redirect to dashboard

### Registration
- `GET /auth/register` - Registration page (HTML)
- `POST /auth/register` - Register a new user

### Todos
- `GET /todos/` - List all Todos (HTML)
- `GET /todos/add-todo` - Display form to add a new Todo (HTML)
- `POST /todos/add-todo` - Create a new Todo
- `GET /todos/edit-todo/{todo_id}` - Display form to edit an existing Todo (HTML)

- `POST /todos/edit-todo/{todo_id}` - Update a specific Todo
- `GET /todos/delete/{todo_id}` - Delete a Todo

### Categories (Admin Only)
- `GET /categories/` - List all Categories (HTML)
- `GET /categories/create` - Display form to create a new Category (HTML)

- `POST /categories/create` - Create a new Category
- `GET /categories/edit/{category_id}` - Display form to edit an existing Category (HTML)

- `POST /categories/edit/{category_id}` - Update a specific Category
- `GET /categories/delete/{category_id}` - Delete a Category

## OpenAPI Documentation

You can view API documentation by visiting:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## License
MIT License