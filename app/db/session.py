import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from typing import Generator

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.warning("DATABASE_URL is not set in environment variables.")
    print("DATABASE_URL is not set in environment variables.")
    # Используем SQLite по умолчанию для демо режима
    DATABASE_URL = "sqlite:///./trading_bot.db"
    logger.info(f"Using default SQLite database: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info(f"Database connection established: {DATABASE_URL}")
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    # Создаем заглушку для случаев, когда БД недоступна
    engine = None
    SessionLocal = None

def get_db() -> Generator[Session, None, None]:
    """
    Зависимость FastAPI для получения сессии БД.
    Гарантирует закрытие сессии после использования.
    """
    if SessionLocal is None:
        logger.error("Database is not available")
        raise RuntimeError("Database connection is not available")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 