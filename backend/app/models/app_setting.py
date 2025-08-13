from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from ..core.database import Base


class AppSetting(Base):
    __tablename__ = "app_settings"
    id = Column(String, primary_key=True)  # use 'global'
    project_name = Column(String(255), nullable=False)
    allow_registration = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
