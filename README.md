# Library Management System

A full-stack Library Management System built with **FastAPI** (backend REST API), **Gradio** (frontend UI), and **SQLAlchemy + SQLite** (database). Supports book cataloging with multiple physical copies, member registration, book issue/return, and automatic fine calculation.

## Features

- **Books & Copies** — catalog titles separately from physical copies, so multiple copies of the same book (e.g. 5 copies of *Harry Potter*) are tracked independently
- **Members** — register and manage library members
- **Issue / Return** — issue a specific copy to a member, return it later, with automatic status tracking
- **Fine Calculation** — 2-day grace period after the due date, then ₹5/day, no cap. Live "current fine" estimate available before a book is returned
- **REST API** — fully documented, interactive API docs via FastAPI's built-in Swagger UI
- **Gradio UI** — simple browser-based frontend for all operations, calling the API over HTTP

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| Frontend | Gradio |
| ORM | SQLAlchemy |
| Database | SQLite (dev) |
| Validation | Pydantic |
| Package management | uv |

## Project Structure

```
library-system/
├── backend/
│   └── library_system/
│       ├── __init__.py
│       ├── main.py                # FastAPI app entrypoint
│       ├── database.py            # DB engine/session setup
│       ├── models.py              # SQLAlchemy ORM models
│       ├── schemas.py             # Pydantic request/response schemas
│       ├── crud.py                 # Database query logic + fine calculation
│       └── routers/
│           ├── books.py
│           ├── members.py
│           └── transactions.py
├── frontend/
│   └── app.py                     # Gradio UI (calls the backend over HTTP)
├── data/                          # Generated SQLite database (git-ignored)
│   └── library.db
├── .gitignore
├── pyproject.toml
└── uv.lock
```

> The backend and frontend are fully decoupled — `frontend/app.py` never imports from `backend/`, it only calls the API over HTTP, exactly like any other client would.

## Data Model

- **Books** — one row per title/edition (title, author, ISBN, etc.)
- **Book Copies** — one row per physical copy, linked to a `Book`. This is what allows the library to own multiple copies of the same title, each independently trackable (available / issued / lost / damaged)
- **Members** — library members with contact info and status
- **Transactions** — the issue/return record, linking a specific copy to a member with due date, return date, and fine amount

## Setup

### Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) installed

### Install dependencies
```bash
uv sync
```

## Running the App

You need two terminals — one for the backend, one for the frontend.

**Terminal 1 — start the backend API:**
```bash
uv run uvicorn library_system.main:app --reload --app-dir backend
```
API will be live at `http://127.0.0.1:8000`. Interactive docs: `http://127.0.0.1:8000/docs`.

**Terminal 2 — start the Gradio frontend:**
```bash
uv run python frontend/app.py
```
Gradio will print a local URL (usually `http://127.0.0.1:7860`) — open it in your browser.

## Fine Policy

- First **2 days** after the due date: no fine
- From **day 3** onward: **₹5/day**
- No maximum cap

## API Overview

| Operation | Method | Endpoint |
|---|---|---|
| Register a member | `POST` | `/members` |
| Add a copy to a book | `POST` | `/books/{book_id}/copies` |
| Issue a book | `POST` | `/transactions` |
| Check current fine | `GET` | `/transactions/{transaction_id}/current-fine` |
| Return a book | `PATCH` | `/transactions/{transaction_id}/return` |

Full endpoint list and request/response schemas available at `/docs` once the backend is running.

## License

This project is for educational purposes.