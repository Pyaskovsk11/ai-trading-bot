import pytest
import asyncio
from app.services.news_relevance_service import NewsRelevanceService

class DummyAIAPIClient:
    def __init__(self, single_response=None, batch_response=None, raise_exc=False):
        self.single_response = single_response or {"relevance_score": 0.7, "relevant_assets": ["BTC"]}
        self.batch_response = batch_response or {"results": [self.single_response]}
        self.raise_exc = raise_exc
        self.calls = []
    async def post(self, endpoint, payload):
        self.calls.append((endpoint, payload))
        if self.raise_exc:
            raise Exception("API error")
        if endpoint == "/relevance":
            return self.single_response
        elif endpoint == "/relevance/batch":
            return self.batch_response
        return {}

@pytest.mark.asyncio
async def test_assess_relevance_single():
    ai_client = DummyAIAPIClient()
    service = NewsRelevanceService(ai_client)
    result = await service.assess_relevance("BTC news", ["BTC", "ETH"])
    assert result["relevance_score"] == 0.7
    assert "BTC" in result["relevant_assets"]

@pytest.mark.asyncio
async def test_assess_relevance_cache():
    ai_client = DummyAIAPIClient()
    service = NewsRelevanceService(ai_client)
    text = "BTC news"
    assets = ["BTC", "ETH"]
    result1 = await service.assess_relevance(text, assets)
    result2 = await service.assess_relevance(text, assets)
    assert result1 == result2
    assert ai_client.calls.count(("/relevance", {"text": text, "assets": assets})) == 1

@pytest.mark.asyncio
async def test_assess_batch():
    ai_client = DummyAIAPIClient(batch_response={"results": [
        {"relevance_score": 1.0, "relevant_assets": ["BTC"]},
        {"relevance_score": 0.0, "relevant_assets": []}
    ]})
    service = NewsRelevanceService(ai_client)
    texts = ["BTC news", "Other news"]
    assets = ["BTC", "ETH"]
    results = await service.assess_batch(texts, assets)
    assert results[0]["relevance_score"] == 1.0
    assert results[1]["relevance_score"] == 0.0

@pytest.mark.asyncio
async def test_assess_relevance_error():
    ai_client = DummyAIAPIClient(raise_exc=True)
    service = NewsRelevanceService(ai_client)
    result = await service.assess_relevance("BTC news", ["BTC"])
    assert result is None 