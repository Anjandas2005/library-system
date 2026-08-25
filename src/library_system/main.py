from fastapi import FastAPI

from . import models
from .database import engine
from .routers import books, members, transactions

# Creates tables on startup if they don't already exist.
# (Fine for dev; in production you'd use a migration tool like Alembic instead.)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Library Management API")

app.include_router(books.router)
app.include_router(members.router)
app.include_router(transactions.router)


@app.get("/")
def health_check():
    return {"status": "ok"}