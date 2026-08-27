import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Ensure the data/ folder exists relative to wherever the app is run from
os.makedirs("data", exist_ok=True)

# SQLite file will be created inside the data/ folder as "library.db"
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/library.db"

# connect_args is SQLite-specific: allows the same connection to be used
# across the multiple threads that FastAPI/Gradio may spawn.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and guarantees it's closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()