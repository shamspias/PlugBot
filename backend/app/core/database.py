from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from .config import settings


class DatabaseManager:
    """Database connection manager."""

    def __init__(self):
        self.engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def get_db(self) -> Generator[Session, None, None]:
        """Get database session."""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


Base = declarative_base()
db_manager = DatabaseManager()
