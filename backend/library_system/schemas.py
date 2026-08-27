from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

from .models import CopyStatus, MembershipType, MemberStatus, TransactionStatus


# ---------- Books ----------

class BookCreate(BaseModel):
    isbn: str
    title: str
    author: str
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    genre: Optional[str] = None


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: int
    isbn: str
    title: str
    author: str
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    genre: Optional[str] = None


# ---------- Book Copies ----------

class BookCopyCreate(BaseModel):
    barcode: str
    shelf_location: Optional[str] = None
    date_acquired: Optional[date] = None


class BookCopyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    copy_id: int
    book_id: int
    barcode: str
    status: CopyStatus
    shelf_location: Optional[str] = None
    date_acquired: Optional[date] = None


# ---------- Members ----------

class MemberCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    membership_type: MembershipType


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    member_id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    membership_type: MembershipType
    join_date: date
    status: MemberStatus


# ---------- Transactions ----------

class TransactionCreate(BaseModel):
    copy_id: int
    member_id: int
    due_date: date


class TransactionReturn(BaseModel):
    return_date: Optional[datetime] = None  # defaults to "now" server-side if omitted


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: int
    copy_id: int
    member_id: int
    issue_date: datetime
    due_date: date
    return_date: Optional[datetime] = None
    fine_amount: Decimal
    status: TransactionStatus