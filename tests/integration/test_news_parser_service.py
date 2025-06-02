import pytest
from sqlalchemy.orm import Session
from app.services.news_parser_service import fetch_and_save_all_news
from app.db.models import NewsArticle
import app.services.arkham_service
import app.services.lookonchain_service

@pytest.mark.asyncio
async def test_fetch_and_save_all_news(monkeypatch, db_session: Session):
    # Мокаем парсеры, чтобы не ходить в интернет
    async def mock_fetch_arkham_news(limit=10):
        return [{
            "title": "Arkham Test",
            "content": "Arkham Content",
            "source": "Arkham",
            "published_at": "2024-06-01T12:00:00",
            "url": "https://intel.arkm.com/test",
            "sentiment_score": 0.0
        }]
    async def mock_fetch_lookonchain_news(limit=10):
        return [{
            "title": "Lookonchain Test",
            "content": "Lookonchain Content",
            "source": "Lookonchain",
            "published_at": "2024-06-01T13:00:00",
            "url": "https://m.lookonchain.com/test",
            "sentiment_score": 0.0
        }]
    monkeypatch.setattr(app.services.arkham_service, "fetch_arkham_news", mock_fetch_arkham_news)
    monkeypatch.setattr(app.services.lookonchain_service, "fetch_lookonchain_news", mock_fetch_lookonchain_news)

    await fetch_and_save_all_news(db_session, limit=1)

    # Проверяем, что новости появились в базе
    arkham = db_session.query(NewsArticle).filter_by(source="Arkham").first()
    lookonchain = db_session.query(NewsArticle).filter_by(source="Lookonchain").first()
    assert arkham is not None
    assert lookonchain is not None
    assert arkham.title == "Arkham Test"
    assert lookonchain.title == "Lookonchain Test" 