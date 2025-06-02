import pytest
import asyncio
from app.services.rag_analysis_service import RAGAnalysisService

@pytest.mark.asyncio
async def test_split_into_chunks():
    service = RAGAnalysisService(ai_client=DummyAIAPIClient())
    chunks = await service.split_into_chunks("Test text for chunking.", chunk_size=5)
    assert isinstance(chunks, list)
    assert len(chunks) > 0

@pytest.mark.asyncio
async def test_generate_embedding():
    service = RAGAnalysisService(ai_client=DummyAIAPIClient())
    embedding = await service.generate_embedding("Test chunk")
    assert isinstance(embedding, list)
    assert all(isinstance(x, float) for x in embedding)

class DummyAIAPIClient:
    def __init__(self, single_response=None, batch_response=None, raise_exc=False):
        self.single_response = single_response or {"summary": "Summary", "chunks": ["chunk1"], "xai_explanation": "Explanation"}
        self.batch_response = batch_response or {"results": [self.single_response]}
        self.raise_exc = raise_exc
        self.calls = []
    async def post(self, endpoint, payload):
        self.calls.append((endpoint, payload))
        if self.raise_exc:
            raise Exception("API error")
        if endpoint == "/rag/analyze":
            return self.single_response
        elif endpoint == "/rag/analyze/batch":
            return self.batch_response
        return {}

@pytest.mark.asyncio
async def test_analyze_single():
    ai_client = DummyAIAPIClient()
    service = RAGAnalysisService(ai_client=ai_client)
    result = await service.analyze("Some text")
    assert result["summary"] == "Summary"
    assert result["chunks"] == ["chunk1"]
    assert result["xai_explanation"] == "Explanation"

@pytest.mark.asyncio
async def test_analyze_cache():
    ai_client = DummyAIAPIClient()
    service = RAGAnalysisService(ai_client=ai_client)
    text = "Some text"
    result1 = await service.analyze(text)
    result2 = await service.analyze(text)
    assert result1 == result2
    assert ai_client.calls.count(("/rag/analyze", {"text": text})) == 1

@pytest.mark.asyncio
async def test_analyze_batch():
    ai_client = DummyAIAPIClient(batch_response={"results": [
        {"summary": "S1", "chunks": ["c1"], "xai_explanation": "E1"},
        {"summary": "S2", "chunks": ["c2"], "xai_explanation": "E2"}
    ]})
    service = RAGAnalysisService(ai_client=ai_client)
    texts = ["Text1", "Text2"]
    results = await service.analyze_batch(texts)
    assert results[0]["summary"] == "S1"
    assert results[1]["summary"] == "S2"

@pytest.mark.asyncio
async def test_analyze_error():
    ai_client = DummyAIAPIClient(raise_exc=True)
    service = RAGAnalysisService(ai_client=ai_client)
    result = await service.analyze("Some text")
    assert result is None

@pytest.mark.asyncio
async def test_split_into_chunks_empty():
    service = RAGAnalysisService(ai_client=DummyAIAPIClient())
    chunks = await service.split_into_chunks("")
    assert isinstance(chunks, list)
    assert len(chunks) == 1 or len(chunks) == 0  # В зависимости от реализации stub

@pytest.mark.asyncio
async def test_analyze_single_error():
    ai_client = DummyAIAPIClient(raise_exc=True)
    service = RAGAnalysisService(ai_client=ai_client)
    result = await service.analyze("Some text")
    assert result is None

@pytest.mark.asyncio
async def test_analyze_batch_partial_error():
    class PartialErrorAIClient(DummyAIAPIClient):
        async def post(self, endpoint, payload):
            if endpoint == "/rag/analyze/batch":
                return {"results": [self.single_response, None]}
            return await super().post(endpoint, payload)
    ai_client = PartialErrorAIClient()
    service = RAGAnalysisService(ai_client=ai_client)
    texts = ["Text1", "Text2"]
    results = await service.analyze_batch(texts)
    assert results[0] is not None
    assert results[1] is None

@pytest.mark.asyncio
async def test_explanation_format():
    ai_client = DummyAIAPIClient(single_response={"summary": "S", "chunks": ["c"], "xai_explanation": {"reason": "test", "sources": ["src1"]}})
    service = RAGAnalysisService(ai_client=ai_client)
    result = await service.analyze("Some text")
    assert isinstance(result["xai_explanation"], dict)
    assert "reason" in result["xai_explanation"]
    assert "sources" in result["xai_explanation"] 