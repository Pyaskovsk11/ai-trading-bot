import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from typing import Generator

load_dotenv()

logger = logging.getLogger(__name__)

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    logger.error("DB_URL is not set in environment variables.")
    raise RuntimeError("DB_URL is required for database connection.")

engine = create_engine(DB_URL, pool_pre_ping=True)
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