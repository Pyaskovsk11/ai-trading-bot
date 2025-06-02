import pytest
from app.services import news_service
from app.schemas.news import NewsCreate
from sqlalchemy.orm import Session

def test_create_and_get_news_article(test_db: Session):
    news_data = {"title": "Test News", "content": "Test content", "source": "UnitTest", "published_at": "2024-01-01T00:00:00", "sentiment_score": 0.5}
    news = news_service.create_news(test_db, NewsCreate(**news_data))
    assert news.title == news_data["title"]
    fetched = news_service.get_news_by_id(test_db, news.id)
    assert fetched is not None
    assert fetched.source == news_data["source"] 