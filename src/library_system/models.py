import enum
from datetime import date, datetime

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, ForeignKey, Enum, Numeric
)
from sqlalchemy.orm import relationship

from .database import Base


class CopyStatus(str, enum.Enum):
    available = "available"
    issued = "issued"
    lost = "lost"
    damaged = "damaged"
    under_repair = "under_repair"


class MembershipType(str, enum.Enum):
    student = "student"
    faculty = "faculty"
    public = "public"


class MemberStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    expired = "expired"


class TransactionStatus(str, enum.Enum):
    issued = "issued"
    returned = "returned"
    overdue = "overdue"
    lost = "lost"


class Book(Base):
    __tablename__ = "books"

    book_id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(13), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    publisher = Column(String(255))
    publication_year = Column(Integer)
    genre = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # One book (title) -> many physical copies
    copies = relationship("BookCopy", back_populates="book", cascade="all, delete-orphan")


class BookCopy(Base):
    __tablename__ = "book_copies"

    copy_id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.book_id"), nullable=False)
    barcode = Column(String(50), unique=True, nullable=False)
    status = Column(Enum(CopyStatus), default=CopyStatus.available, nullable=False)
    shelf_location = Column(String(50))
    date_acquired = Column(Date, default=date.today)

    book = relationship("Book", back_populates="copies")
    transactions = relationship("Transaction", back_populates="copy")


class Member(Base):
    __tablename__ = "members"

    member_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20))
    membership_type = Column(Enum(MembershipType), nullable=False)
    join_date = Column(Date, default=date.today)
    status = Column(Enum(MemberStatus), default=MemberStatus.active)

    transactions = relationship("Transaction", back_populates="member")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    copy_id = Column(Integer, ForeignKey("book_copies.copy_id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.member_id"), nullable=False)
    issue_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(Date, nullable=False)
    return_date = Column(DateTime, nullable=True)
    fine_amount = Column(Numeric(10, 2), default=0)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.issued)

    copy = relationship("BookCopy", back_populates="transactions")
    member = relationship("Member", back_populates="transactions")