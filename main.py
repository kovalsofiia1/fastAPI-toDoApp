from fastapi import FastAPI, Depends
from starlette.responses import RedirectResponse

from routers import auth, todos, categories
from starlette.staticfiles import StaticFiles

app = FastAPI(debug=True,
              title="Мій Todo API",
              description="Цей API дозволяє керувати списком завдань.",
              version="1.0.1",
              contact={
                  "name": "Підтримка",
                  "email": "support@example.com",
              },
              license_info={
                  "name": "MIT",
                  "url": "https://opensource.org/licenses/MIT",
              },
              )


app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(todos.router)

app.include_router(categories.router)
@app.get("/", include_in_schema=False)  # Exclude from OpenAPI docs
async def root():
    return RedirectResponse(url="/todos")
