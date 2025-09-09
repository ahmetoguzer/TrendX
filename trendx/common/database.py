"""Database connection and session management."""

from contextlib import contextmanager
from typing import Generator

from sqlmodel import SQLModel, create_engine, Session

from .config import settings


# Create engine
engine = create_engine(
    settings.database.url,
    echo=False,  # Set to True for SQL debugging
    connect_args={"check_same_thread": False} if "sqlite" in settings.database.url else {},
)


def create_tables() -> None:
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
