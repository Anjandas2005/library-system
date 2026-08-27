from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("", response_model=schemas.TransactionOut, status_code=201)
def issue_book(txn: schemas.TransactionCreate, db: Session = Depends(get_db)):
    result, error = crud.issue_book(db, txn)
    if error is not None:
        # "not found" errors -> 404, everything else (already issued, inactive member) -> 409 Conflict
        status_code = 404 if "not found" in error.lower() else 409
        raise HTTPException(status_code=status_code, detail=error)
    return result


@router.get("", response_model=list[schemas.TransactionOut])
def list_transactions(
    skip: int = 0,
    limit: int = 100,
    status: models.TransactionStatus | None = None,
    db: Session = Depends(get_db),
):
    return crud.list_transactions(db, skip, limit, status)


@router.get("/{transaction_id}", response_model=schemas.TransactionOut)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    txn = crud.get_transaction(db, transaction_id)
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return txn


@router.get("/{transaction_id}/current-fine")
def get_current_fine(transaction_id: int, db: Session = Depends(get_db)):
    """Live estimate: 'if this book were returned right now, what would the fine be?'"""
    txn = crud.get_transaction(db, transaction_id)
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    if txn.return_date is not None:
        return {"transaction_id": transaction_id, "fine_amount": txn.fine_amount, "final": True}

    estimated_fine = crud.calculate_fine(txn.due_date, as_of=datetime.utcnow())
    return {"transaction_id": transaction_id, "fine_amount": estimated_fine, "final": False}


@router.patch("/{transaction_id}/return", response_model=schemas.TransactionOut)
def return_book(
    transaction_id: int,
    return_data: schemas.TransactionReturn,
    db: Session = Depends(get_db),
):
    result, error = crud.return_book(db, transaction_id, return_data)
    if error is not None:
        status_code = 404 if "not found" in error.lower() else 409
        raise HTTPException(status_code=status_code, detail=error)
    return result