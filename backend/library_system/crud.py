from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from . import models, schemas

GRACE_PERIOD_DAYS = 2
FINE_PER_DAY = Decimal("5.00")


# ---------- Fine calculation ----------

def calculate_fine(due_date: date, as_of: datetime | None = None) -> Decimal:
    """
    First GRACE_PERIOD_DAYS days after due_date: no fine.
    Every day after that: FINE_PER_DAY. No cap.
    """
    if as_of is None:
        as_of = datetime.utcnow()

    days_overdue = (as_of.date() - due_date).days

    if days_overdue <= GRACE_PERIOD_DAYS:
        return Decimal("0.00")

    chargeable_days = days_overdue - GRACE_PERIOD_DAYS
    return FINE_PER_DAY * chargeable_days


# ---------- Books ----------

def create_book(db: Session, book: schemas.BookCreate) -> models.Book:
    db_book = models.Book(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def get_book(db: Session, book_id: int) -> models.Book | None:
    return db.query(models.Book).filter(models.Book.book_id == book_id).first()


def list_books(db: Session, skip: int = 0, limit: int = 100) -> list[models.Book]:
    return db.query(models.Book).offset(skip).limit(limit).all()


def search_books(
    db: Session,
    title: str | None = None,
    author: str | None = None,
    genre: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[models.Book]:
    """
    Case-insensitive partial match on any combination of title, author, genre.
    If none of the filters are provided, behaves exactly like list_books.
    """
    query = db.query(models.Book)

    if title:
        query = query.filter(models.Book.title.ilike(f"%{title}%"))
    if author:
        query = query.filter(models.Book.author.ilike(f"%{author}%"))
    if genre:
        query = query.filter(models.Book.genre.ilike(f"%{genre}%"))

    return query.offset(skip).limit(limit).all()


# ---------- Book Copies ----------

def add_book_copy(db: Session, book_id: int, copy: schemas.BookCopyCreate) -> models.BookCopy | None:
    book = get_book(db, book_id)
    if book is None:
        return None

    db_copy = models.BookCopy(book_id=book_id, **copy.model_dump())
    db.add(db_copy)
    db.commit()
    db.refresh(db_copy)
    return db_copy


def get_copy(db: Session, copy_id: int) -> models.BookCopy | None:
    return db.query(models.BookCopy).filter(models.BookCopy.copy_id == copy_id).first()


def list_copies_for_book(db: Session, book_id: int) -> list[models.BookCopy]:
    return db.query(models.BookCopy).filter(models.BookCopy.book_id == book_id).all()


# ---------- Members ----------

def create_member(db: Session, member: schemas.MemberCreate) -> models.Member:
    db_member = models.Member(**member.model_dump())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


def get_member(db: Session, member_id: int) -> models.Member | None:
    return db.query(models.Member).filter(models.Member.member_id == member_id).first()


def list_members(db: Session, skip: int = 0, limit: int = 100) -> list[models.Member]:
    return db.query(models.Member).offset(skip).limit(limit).all()


# ---------- Transactions ----------

def issue_book(db: Session, txn: schemas.TransactionCreate) -> tuple[models.Transaction | None, str | None]:
    """
    Returns (transaction, error_message). If error_message is not None, the
    transaction was NOT created and the caller should surface that error.
    """
    copy = get_copy(db, txn.copy_id)
    if copy is None:
        return None, "Copy not found."
    if copy.status != models.CopyStatus.available:
        return None, f"Copy is not available (current status: {copy.status.value})."

    member = get_member(db, txn.member_id)
    if member is None:
        return None, "Member not found."
    if member.status != models.MemberStatus.active:
        return None, f"Member is not active (current status: {member.status.value})."

    db_txn = models.Transaction(
        copy_id=txn.copy_id,
        member_id=txn.member_id,
        due_date=txn.due_date,
        status=models.TransactionStatus.issued,
    )
    copy.status = models.CopyStatus.issued

    db.add(db_txn)
    db.commit()
    db.refresh(db_txn)
    return db_txn, None


def get_transaction(db: Session, transaction_id: int) -> models.Transaction | None:
    return db.query(models.Transaction).filter(
        models.Transaction.transaction_id == transaction_id
    ).first()


def get_open_transaction_for_copy(db: Session, copy_id: int) -> models.Transaction | None:
    """Find the currently-issued (not yet returned) transaction for a copy."""
    return db.query(models.Transaction).filter(
        models.Transaction.copy_id == copy_id,
        models.Transaction.return_date.is_(None),
    ).first()


def return_book(
    db: Session, transaction_id: int, return_data: schemas.TransactionReturn
) -> tuple[models.Transaction | None, str | None]:
    txn = get_transaction(db, transaction_id)
    if txn is None:
        return None, "Transaction not found."
    if txn.return_date is not None:
        return None, "This book has already been returned."

    return_date = return_data.return_date or datetime.utcnow()
    fine = calculate_fine(txn.due_date, as_of=return_date)

    txn.return_date = return_date
    txn.fine_amount = fine
    txn.status = models.TransactionStatus.returned

    copy = get_copy(db, txn.copy_id)
    if copy is not None:
        copy.status = models.CopyStatus.available

    db.commit()
    db.refresh(txn)
    return txn, None


def list_transactions(
    db: Session, skip: int = 0, limit: int = 100, status: models.TransactionStatus | None = None
) -> list[models.Transaction]:
    query = db.query(models.Transaction)
    if status is not None:
        query = query.filter(models.Transaction.status == status)
    return query.offset(skip).limit(limit).all()