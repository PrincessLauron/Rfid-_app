from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator
import os

# Database location (relative to project root)
DEFAULT_SQLITE_PATH = os.getenv("AMS_SQLITE_PATH", "backend/app/app.db")
DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"

# SQLite specific: check_same_thread=False is needed for default SQLite driver in multi-threaded apps
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


