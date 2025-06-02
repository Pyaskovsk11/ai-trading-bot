import pytest
from app.services.ner_service import NERService

class DummyAIAPIClient:
    def __init__(self, single_response=None, batch_response=None, raise_exc=False):
        self.single_response = single_response or {"entities": [{"text": "BTC", "type": "CRYPTO", "start": 0, "end": 3}]}
        self.batch_response = batch_response or {"results": [self.single_response]}
        self.raise_exc = raise_exc
        self.calls = []
    async def post(self, endpoint, payload):
        self.calls.append((endpoint, payload))
        if self.raise_exc:
            raise Exception("API error")
        if endpoint == "/ner":
            return self.single_response
        elif endpoint == "/ner/batch":
            return self.batch_response
        return {}

@pytest.mark.asyncio
async def test_extract_entities_single():
    ai_client = DummyAIAPIClient()
    service = NERService(ai_client)
    result = await service.extract_entities("BTC to the moon!")
    assert "entities" in result
    assert result["entities"][0]["text"] == "BTC"

@pytest.mark.asyncio
async def test_extract_entities_cache():
    ai_client = DummyAIAPIClient()
    service = NERService(ai_client)
    text = "BTC to the moon!"
    result1 = await service.extract_entities(text)
    result2 = await service.extract_entities(text)
    assert result1 == result2
    assert ai_client.calls.count(("/ner", {"text": text})) == 1

@pytest.mark.asyncio
async def test_extract_batch():
    ai_client = DummyAIAPIClient(batch_response={"results": [
        {"entities": [{"text": "BTC", "type": "CRYPTO"}]},
        {"entities": [{"text": "ETH", "type": "CRYPTO"}]}
    ]})
    service = NERService(ai_client)
    texts = ["BTC to the moon!", "ETH upgrade"]
    results = await service.extract_batch(texts)
    assert results[0]["entities"][0]["text"] == "BTC"
    assert results[1]["entities"][0]["text"] == "ETH"

@pytest.mark.asyncio
async def test_extract_entities_error():
    ai_client = DummyAIAPIClient(raise_exc=True)
    service = NERService(ai_client)
    result = await service.extract_entities("BTC to the moon!")
    assert result is None 