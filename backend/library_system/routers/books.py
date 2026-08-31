from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/books", tags=["Books"])


@router.post("", response_model=schemas.BookOut, status_code=201)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    return crud.create_book(db, book)


@router.get("", response_model=list[schemas.BookOut])
def list_books(
    title: str | None = None,
    author: str | None = None,
    genre: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Lists books. If title, author, or genre are provided, filters
    results using a case-insensitive partial match on those fields.
    """
    return crud.search_books(db, title=title, author=author, genre=genre, skip=skip, limit=limit)


@router.get("/{book_id}", response_model=schemas.BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = crud.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found.")
    return book


@router.post("/{book_id}/copies", response_model=schemas.BookCopyOut, status_code=201)
def add_book_copy(book_id: int, copy: schemas.BookCopyCreate, db: Session = Depends(get_db)):
    db_copy = crud.add_book_copy(db, book_id, copy)
    if db_copy is None:
        raise HTTPException(status_code=404, detail="Book not found.")
    return db_copy


@router.get("/{book_id}/copies", response_model=list[schemas.BookCopyOut])
def list_book_copies(book_id: int, db: Session = Depends(get_db)):
    book = crud.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found.")
    return crud.list_copies_for_book(db, book_id)