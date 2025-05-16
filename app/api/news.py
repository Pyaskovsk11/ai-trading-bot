from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import logging
from app.db.session import get_db
from app.schemas.news import NewsCreate, NewsRead, NewsUpdate, NewsList
from app.services import news_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["News"])

@router.get("/", response_model=NewsList)
def list_news(
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(100, ge=1, le=500, description="Максимум записей на страницу"),
    db: Session = Depends(get_db)
) -> NewsList:
    """
    Получить список новостей с пагинацией.
    """
    items, total = news_service.get_news(db, skip=skip, limit=limit)
    page = (skip // limit) + 1 if limit else 1
    pages = (total + limit - 1) // limit if limit else 1
    return NewsList(items=items, total=total, page=page, size=limit, pages=pages)

@router.get("/{news_id}", response_model=NewsRead)
def get_news(news_id: int, db: Session = Depends(get_db)) -> NewsRead:
    """
    Получить новость по ID.
    """
    news = news_service.get_news_by_id(db, news_id)
    if not news:
        logger.warning(f"News {news_id} not found.")
        raise HTTPException(status_code=404, detail="News not found")
    return news

@router.post("/", response_model=NewsRead, status_code=status.HTTP_201_CREATED)
def create_news(news_in: NewsCreate, db: Session = Depends(get_db)) -> NewsRead:
    """
    Создать новую новость.
    """
    news = news_service.create_news(db, news_in)
    return news

@router.put("/{news_id}", response_model=NewsRead)
def update_news(news_id: int, news_in: NewsUpdate, db: Session = Depends(get_db)) -> NewsRead:
    """
    Обновить новость по ID.
    """
    news = news_service.update_news(db, news_id, news_in)
    if not news:
        logger.warning(f"News {news_id} not found for update.")
        raise HTTPException(status_code=404, detail="News not found")
    return news

@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_news(news_id: int, db: Session = Depends(get_db)) -> None:
    """
    Удалить новость по ID.
    """
    success = news_service.delete_news(db, news_id)
    if not success:
        logger.warning(f"News {news_id} not found for delete.")
        raise HTTPException(status_code=404, detail="News not found") 