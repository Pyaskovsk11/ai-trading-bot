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
    logger.error("DATABASE_URL is not set in environment variables.")
    raise RuntimeError("DATABASE_URL is required for database connection.")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Зависимость FastAPI для получения сессии БД.
    Гарантирует закрытие сессии после использования.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 