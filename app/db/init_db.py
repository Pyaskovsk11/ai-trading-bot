import logging
from sqlalchemy.orm import Session
from app.db.models import Base
from app.db.session import engine

logger = logging.getLogger(__name__)

def init_db() -> None:
    """
    Инициализация базы данных.
    Создает все таблицы, если они не существуют.
    """
    try:
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise 