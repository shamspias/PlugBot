from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class BotBase(BaseModel):
    """Base bot schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    dify_endpoint: str = Field(..., min_length=1)
    dify_type: str = Field(default="chat", pattern="^(chat|agent|chatflow|workflow)$")
    response_mode: str = Field(default="streaming", pattern="^(streaming|blocking)$")
    auto_generate_title: bool = True
    enable_file_upload: bool = True

    # Authentication settings
    auth_required: bool = False
    allowed_email_domains: Optional[str] = None  # Comma-separated domains like "algolyzer.com,google.com"


class BotCreate(BotBase):
    """Schema for creating a bot."""
    dify_api_key: str = Field(..., min_length=1)
    telegram_bot_token: Optional[str] = None

    @field_validator('dify_endpoint')
    def validate_endpoint(cls, v: str):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Endpoint must start with http:// or https://')
        return v.rstrip('/')

    @field_validator('dify_api_key')
    def strip_and_require_api_key(cls, v: str):
        v = v.strip()
        if not v:
            raise ValueError('Dify API key cannot be empty')
        return v

    @field_validator('telegram_bot_token')
    def strip_optional_telegram_token(cls, v: Optional[str]):
        if v is None:
            return v
        v = v.strip()
        # Treat empty string as None
        return v or None

    @field_validator('allowed_email_domains')
    def validate_email_domains(cls, v: Optional[str]):
        if v is None or v.strip() == '':
            return None
        # Clean and validate domain format
        domains = [d.strip().lower() for d in v.split(',')]
        for domain in domains:
            if not domain:
                continue
            # Remove @ if present and validate basic domain format
            domain = domain.lstrip('@')
            if '.' not in domain or len(domain) < 3:
                raise ValueError(f'Invalid domain format: {domain}')
        return ','.join(domains)


class BotUpdate(BaseModel):
    """Schema for updating a bot."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    dify_endpoint: Optional[str] = None
    dify_api_key: Optional[str] = None
    dify_type: Optional[str] = Field(None, pattern="^(chat|agent|chatflow|workflow)$")
    telegram_bot_token: Optional[str] = None
    response_mode: Optional[str] = Field(None, pattern="^(streaming|blocking)$")
    auto_generate_title: Optional[bool] = None
    enable_file_upload: Optional[bool] = None
    is_active: Optional[bool] = None
    auth_required: Optional[bool] = None
    allowed_email_domains: Optional[str] = None

    @field_validator('dify_endpoint')
    def normalize_endpoint(cls, v: Optional[str]):
        if v is None:
            return v
        v = v.strip()
        return v.rstrip('/')

    @field_validator('dify_api_key', 'telegram_bot_token', mode='before')
    def empty_string_to_none(cls, v):
        # If the user leaves a secret blank in the edit form, treat it as "no change"
        if isinstance(v, str):
            v = v.strip()
            if v == '':
                return None
        return v

    @field_validator('allowed_email_domains')
    def validate_email_domains(cls, v: Optional[str]):
        if v is None or v.strip() == '':
            return None
        domains = [d.strip().lower() for d in v.split(',')]
        for domain in domains:
            if not domain:
                continue
            domain = domain.lstrip('@')
            if '.' not in domain or len(domain) < 3:
                raise ValueError(f'Invalid domain format: {domain}')
        return ','.join(domains)


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
