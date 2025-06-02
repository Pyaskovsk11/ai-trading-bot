import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from app.services.sentiment_service import SentimentService
from app.services.ai_api_client import AIAPIClient

class DummyAIAPIClient:
    def __init__(self, single_response=None, batch_response=None, raise_exc=False):
        self.single_response = single_response or {"sentiment_score": 0.5, "label": "neutral", "confidence": 0.9}
        self.batch_response = batch_response or {"results": [self.single_response]}
        self.raise_exc = raise_exc
        self.calls = []
    async def post(self, endpoint, payload):
        self.calls.append((endpoint, payload))
        if self.raise_exc:
            raise Exception("API error")
        if endpoint == "/sentiment":
            return self.single_response
        elif endpoint == "/sentiment/batch":
            return self.batch_response
        return {}

@pytest.mark.asyncio
async def test_analyze_sentiment_single():
    ai_client = DummyAIAPIClient()
    service = SentimentService(ai_client)
    result = await service.analyze_sentiment("Test text")
    assert result["sentiment_score"] == 0.5
    assert result["label"] == "neutral"
    assert result["confidence"] == 0.9

@pytest.mark.asyncio
async def test_analyze_sentiment_cache():
    ai_client = DummyAIAPIClient()
    service = SentimentService(ai_client)
    text = "Test text"
    # Первый вызов — не из кэша
    result1 = await service.analyze_sentiment(text)
    # Второй вызов — из кэша
    result2 = await service.analyze_sentiment(text)
    assert result1 == result2
    assert ai_client.calls.count(("/sentiment", {"text": text})) == 1

@pytest.mark.asyncio
async def test_analyze_batch():
    ai_client = DummyAIAPIClient(batch_response={"results": [
        {"sentiment_score": 1.0, "label": "positive", "confidence": 0.95},
        {"sentiment_score": -1.0, "label": "negative", "confidence": 0.8}
    ]})
    service = SentimentService(ai_client)
    texts = ["Good news", "Bad news"]
    results = await service.analyze_batch(texts)
    assert results[0]["label"] == "positive"
    assert results[1]["label"] == "negative"

@pytest.mark.asyncio
async def test_analyze_sentiment_error():
    ai_client = DummyAIAPIClient(raise_exc=True)
    service = SentimentService(ai_client)
    result = await service.analyze_sentiment("Test text")
    assert result is None 