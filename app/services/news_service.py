import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.models import NewsArticle
from app.schemas.news import NewsCreate, NewsUpdate
from datetime import datetime

logger = logging.getLogger(__name__)


def get_news(db: Session, skip: int = 0, limit: int = 100) -> Tuple[List[NewsArticle], int]:
    """
    Получить список новостей с пагинацией.
    """
    try:
        query = db.query(NewsArticle)
        total = query.count()
        items = query.order_by(NewsArticle.published_at.desc()).offset(skip).limit(limit).all()
        return items, total
    except SQLAlchemyError as e:
        logger.error(f"Error fetching news: {e}")
        return [], 0

def get_news_by_id(db: Session, news_id: int) -> Optional[NewsArticle]:
    """
    Получить новость по ID.
    """
    return db.query(NewsArticle).filter(NewsArticle.id == news_id).first()

def create_news(db: Session, news_in: NewsCreate) -> Optional[NewsArticle]:
    """
    Создать новую новость.
    """
    if news_in.sentiment_score is not None and not -1 <= news_in.sentiment_score <= 1:
        logger.error("Sentiment score must be between -1 and 1")
        return None
    try:
        db_news = NewsArticle(
            title=news_in.title,
            content=news_in.content,
            source=news_in.source,
            published_at=news_in.published_at,
            fetched_at=news_in.fetched_at or datetime.utcnow(),
            sentiment_score=news_in.sentiment_score,
            processed=news_in.processed if news_in.processed is not None else False,
            url=str(news_in.url) if news_in.url else None,
            affected_assets=news_in.affected_assets,
        )
        db.add(db_news)
        db.commit()
        db.refresh(db_news)
        return db_news
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating news: {e}")
        return None

def update_news(db: Session, news_id: int, news_in: NewsUpdate) -> Optional[NewsArticle]:
    """
    Обновить новость по ID.
    """
    db_news = db.query(NewsArticle).filter(NewsArticle.id == news_id).first()
    if not db_news:
        return None
    try:
        for field, value in news_in.dict(exclude_unset=True).items():
            setattr(db_news, field, value)
        db.commit()
        db.refresh(db_news)
        return db_news
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating news: {e}")
        return None

def delete_news(db: Session, news_id: int) -> bool:
    """
    Удалить новость по ID.
    """
    db_news = db.query(NewsArticle).filter(NewsArticle.id == news_id).first()
    if not db_news:
        return False
    try:
        db.delete(db_news)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting news: {e}")
        return False 