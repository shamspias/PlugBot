from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .core.config import settings
from .core.database import Base, db_manager
from .api.v1 import bots
from .services.bot_manager import bot_manager
from .models.bot import Bot
from .utils.logger import get_logger
from sqlalchemy.orm import Session

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting application...")

    # Create database tables
    Base.metadata.create_all(bind=db_manager.engine)

    # Start active bots
    db: Session = next(db_manager.get_db())
    active_bots = db.query(Bot).filter(
        Bot.is_active == True,
        Bot.telegram_bot_token != None
    ).all()

    for bot in active_bots:
        try:
            await bot_manager.start_bot(bot, db)
            logger.info(f"Started bot: {bot.name}")
        except Exception as e:
            logger.error(f"Failed to start bot {bot.name}: {str(e)}")

    db.close()

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await bot_manager.stop_all()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(bots.router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
