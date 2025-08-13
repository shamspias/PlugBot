from pydantic import BaseModel
from typing import Optional


class SettingsResponse(BaseModel):
    project_name: str
    allow_registration: bool

    class Config: from_attributes = True


class SettingsUpdate(BaseModel):
    project_name: Optional[str] = None
    allow_registration: Optional[bool] = None
