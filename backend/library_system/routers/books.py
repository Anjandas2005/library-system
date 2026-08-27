from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/books", tags=["Books"])


@router.post("", response_model=schemas.BookOut, status_code=201)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    return crud.create_book(db, book)


@router.get("", response_model=list[schemas.BookOut])
def list_books(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.list_books(db, skip, limit)


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