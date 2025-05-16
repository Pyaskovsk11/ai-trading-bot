import pytest
from app.services import user_service, news_service
from sqlalchemy.orm import Session

def test_create_and_get_user(test_db: Session):
    user_data = {"telegram_id": "999999", "username": "testuser", "is_whitelisted": True}
    user = user_service.create_user(test_db, **user_data)
    assert user.telegram_id == user_data["telegram_id"]
    fetched = user_service.get_user_by_telegram_id(test_db, user_data["telegram_id"])
    assert fetched is not None
    assert fetched.username == user_data["username"]

def test_create_and_get_news(test_db: Session):
    news_data = {"title": "Test News", "source": "UnitTest", "published_at": "2024-01-01T00:00:00", "sentiment_score": 0.5}
    news = news_service.create_news(test_db, **news_data)
    assert news.title == news_data["title"]
    fetched = news_service.get_news_by_id(test_db, news.id)
    assert fetched is not None
    assert fetched.source == news_data["source"] 