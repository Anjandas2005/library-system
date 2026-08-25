from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite file will be created in your project root as "library.db"
SQLALCHEMY_DATABASE_URL = "sqlite:///./library.db"

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