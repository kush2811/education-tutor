"""Database connection engine and session factory."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

engine_kwargs = {}
if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    **engine_kwargs,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
