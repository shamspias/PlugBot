from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from .core.config import settings
from .core.database import Base, db_manager
from .api.v1 import bots, conversations, webhooks, auth
from .services.bot_manager import bot_manager
from .models.bot import Bot
from .utils.logger import get_logger
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting PlugBot application...")

    # Create database tables
    try:
        Base.metadata.create_all(bind=db_manager.engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise

    # Start active bots
    db: Session = next(db_manager.get_db())
    try:
        active_bots = db.query(Bot).filter(
            Bot.is_active == True,
            Bot.telegram_bot_token != None
        ).all()

        logger.info(f"Found {len(active_bots)} active bots to start")

        # Start bots concurrently
        start_tasks = []
        for bot in active_bots:
            start_tasks.append(start_bot_safely(bot, db))

        if start_tasks:
            results = await asyncio.gather(*start_tasks, return_exceptions=True)
            for bot, result in zip(active_bots, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to start bot {bot.name}: {str(result)}")
                else:
                    logger.info(f"Successfully started bot: {bot.name}")
    finally:
        db.close()

    yield

    # Shutdown
    logger.info("Shutting down PlugBot application...")
    await bot_manager.stop_all()
    logger.info("All bots stopped successfully")


async def start_bot_safely(bot: Bot, db: Session):
    """Safely start a bot with error handling."""
    try:
        return await bot_manager.start_bot(bot, db)
    except Exception as e:
        logger.error(f"Error starting bot {bot.name}: {str(e)}")
        return e


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add Trusted Host middleware to prevent host header attacks
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure this based on your domains
)

# Configure CORS with explicit HTTPS support
cors_origins = settings.BACKEND_CORS_ORIGINS

# Ensure HTTPS versions of origins are included
https_origins = []
for origin in cors_origins:
    https_origins.append(origin)
    # If an HTTP origin is specified, also add its HTTPS version
    if origin.startswith("http://"):
        https_origins.append(origin.replace("http://", "https://"))
    # If no protocol is specified, add both
    elif not origin.startswith("https://") and not origin.startswith("http://"):
        https_origins.append(f"https://{origin}")
        https_origins.append(f"http://{origin}")

# Add localhost for development
if settings.DEBUG:
    https_origins.extend([
        "http://localhost:3000",
        "http://localhost:3514",
        "http://localhost:3001",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=https_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(bots.router, prefix=settings.API_V1_STR)
app.include_router(conversations.router, prefix=settings.API_V1_STR)
app.include_router(webhooks.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs_url": "/docs",
        "api_base": settings.API_V1_STR
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for monitoring."""
    db: Session = next(db_manager.get_db())
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    finally:
        db.close()

    # Get running bots count
    running_bots = len(bot_manager.bots)

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "running_bots": running_bots,
        "version": settings.VERSION
    }


@app.get("/api/v1", tags=["api"])
async def api_info():
    """API v1 information endpoint."""
    return {
        "version": "v1",
        "endpoints": {
            "bots": f"{settings.API_V1_STR}/bots",
            "conversations": f"{settings.API_V1_STR}/conversations",
            "webhooks": f"{settings.API_V1_STR}/webhooks",
        }
    }
