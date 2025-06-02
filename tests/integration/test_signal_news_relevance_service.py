import pytest
from app.services import signal_service, news_service, signal_news_relevance_service
from app.schemas.signal import SignalCreate
from app.schemas.news import NewsCreate
from app.schemas.signal_news_relevance import SignalNewsRelevanceCreate
from sqlalchemy.orm import Session

def test_create_and_get_signal_news_relevance(test_db: Session):
    signal = signal_service.create_signal(test_db, SignalCreate(symbol="BTCUSDT", direction="BUY", confidence=0.8, source="unit_test", asset_pair="BTC/USDT", signal_type="BUY", confidence_score=0.9, price_at_signal=50000.0, time_frame="1h", status="NEW"))
    news = news_service.create_news(test_db, NewsCreate(title="Test News", content="Test content", source="UnitTest", published_at="2024-01-01T00:00:00", sentiment_score=0.5))
    rel_data = {"signal_id": signal.id, "news_id": news.id, "relevance_score": 0.8, "impact_type": "POSITIVE"}
    rel = signal_news_relevance_service.create_signal_news_relevance(test_db, SignalNewsRelevanceCreate(**rel_data))
    assert rel.signal_id == signal.id
    fetched = signal_news_relevance_service.get_signal_news_relevance_by_id(test_db, rel.id)
    assert fetched is not None
    assert fetched.news_id == news.id 