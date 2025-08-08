from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
from secrets import token_urlsafe


class Settings(BaseSettings):
    """Application settings configuration."""

    # Application
    PROJECT_NAME: str = "PlugBot"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Security
    SECRET_KEY: str = Field(
        default_factory=lambda: token_urlsafe(32),  # auto if env empty
        env="SECRET_KEY",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    ENCRYPTION_KEY: str = Field(
        default_factory=lambda: token_urlsafe(32)[:32],
        env="ENCRYPTION_KEY",
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@db:5432/plugbot",
        env="DATABASE_URL"
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://redis:6379/0",
        env="REDIS_URL"
    )

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3514"],
        env="BACKEND_CORS_ORIGINS",
    )

    # Telegram
    TELEGRAM_WEBHOOK_URL: Optional[str] = Field(None, env="TELEGRAM_WEBHOOK_URL")

    # Encryption for sensitive data
    ENCRYPTION_KEY: str = Field(..., env="ENCRYPTION_KEY")

    # SMTP (for email-based auth codes)
    SMTP_HOST: str | None = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: str | None = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: str | None = Field(default=None, env="SMTP_PASSWORD")
    SMTP_FROM: str = Field(default="no-reply@yourdomain.com", env="SMTP_FROM")
    SMTP_STARTTLS: bool = Field(default=True, env="SMTP_STARTTLS")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
