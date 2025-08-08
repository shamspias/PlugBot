from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class BotBase(BaseModel):
    """Base bot schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    dify_endpoint: str = Field(..., min_length=1)
    dify_type: str = Field(default="chat", pattern="^(chat|agent|chatflow|workflow)$")
    response_mode: str = Field(default="streaming", pattern="^(streaming|blocking)$")
    max_tokens: int = Field(default=2000, ge=100, le=10000)
    temperature: int = Field(default=7, ge=0, le=10)
    auto_generate_title: bool = True
    enable_file_upload: bool = True


class BotCreate(BotBase):
    """Schema for creating a bot."""
    dify_api_key: str = Field(..., min_length=1)
    telegram_bot_token: Optional[str] = None

    @field_validator('dify_endpoint')
    def validate_endpoint(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Endpoint must start with http:// or https://')
        return v.rstrip('/')


class BotUpdate(BaseModel):
    """Schema for updating a bot."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    dify_endpoint: Optional[str] = None
    dify_api_key: Optional[str] = None
    dify_type: Optional[str] = Field(None, pattern="^(chat|agent|chatflow|workflow)$")
    telegram_bot_token: Optional[str] = None
    response_mode: Optional[str] = Field(None, pattern="^(streaming|blocking)$")
    max_tokens: Optional[int] = Field(None, ge=100, le=10000)
    temperature: Optional[int] = Field(None, ge=0, le=10)
    auto_generate_title: Optional[bool] = None
    enable_file_upload: Optional[bool] = None
    is_active: Optional[bool] = None


class BotResponse(BotBase):
    """Bot response schema."""
    id: str
    is_active: bool
    is_telegram_connected: bool
    telegram_bot_username: Optional[str] = None
    last_health_check: Optional[datetime] = None
    health_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BotStatus(BaseModel):
    """Bot status schema."""
    id: str
    name: str
    is_active: bool
    is_telegram_connected: bool
    health_status: str
    last_health_check: Optional[datetime] = None
    is_running: bool
    conversation_count: int = 0
