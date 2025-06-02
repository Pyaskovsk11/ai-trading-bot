import pytest
from sqlalchemy.orm import Session
from app.db.models import NewsArticle
from app.services.news_ai_processing_service import NewsAIProcessingService
import datetime

class DummySentimentService:
    async def analyze_sentiment(self, text):
        return {"sentiment_score": 0.8, "label": "positive"}

class DummyNERService:
    async def extract_entities(self, text):
        return {"entities": [{"text": "BTC", "type": "CRYPTO"}]}

class DummyRelevanceService:
    async def assess_relevance(self, text, assets):
        return {"relevance_score": 0.9, "relevant_assets": ["BTC"]}

class DummyRAGService:
    async def analyze(self, text):
        return {"summary": "BTC news summary", "chunks": ["chunk1"], "xai_explanation": "XAI details"}

@pytest.mark.asyncio
async def test_news_ai_processing(db_session: Session):
    # Добавляем новость
    news = NewsArticle(
        title="AI test",
        content="Bitcoin вырос на 10% после новости о запуске ETF.",
        source="TestSource",
        published_at=datetime.datetime(2024, 6, 1, 12, 0, 0),
        fetched_at=datetime.datetime(2024, 6, 1, 12, 0, 0),
    )
    db_session.add(news)
    db_session.commit()
    db_session.refresh(news)

    service = NewsAIProcessingService(
        db_session,
        DummySentimentService(),
        DummyNERService(),
        DummyRelevanceService(),
        DummyRAGService()
    )
    updated_news = await service.process_news(news.id)
    assert updated_news is not None
    assert updated_news.sentiment_score == 0.8
    if hasattr(updated_news, "extracted_entities"):
        assert updated_news.extracted_entities == [{"text": "BTC", "type": "CRYPTO"}]
    if hasattr(updated_news, "relevance_score"):
        assert updated_news.relevance_score == 0.9
    if hasattr(updated_news, "summary"):
        assert updated_news.summary == "BTC news summary"
    if hasattr(updated_news, "xai_explanation"):
        assert updated_news.xai_explanation == "XAI details" 