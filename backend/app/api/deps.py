from fastapi import Depends
from sqlalchemy.orm import Session
from ..core.database import db_manager


def get_db() -> Session:
    """Yield a DB session that closes automatically."""
    return next(db_manager.get_db())
