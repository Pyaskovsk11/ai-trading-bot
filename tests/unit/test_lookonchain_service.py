import pytest
import asyncio
from app.services.lookonchain_service import fetch_lookonchain_news

@pytest.mark.asyncio
async def test_fetch_lookonchain_news(monkeypatch):
    class MockResponse:
        text = '<div class="news-card">Test Lookonchain News</div>'
        def raise_for_status(self):
            pass
    class MockClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def get(self, url):
            return MockResponse()
    monkeypatch.setattr("httpx.AsyncClient", lambda *a, **kw: MockClient())
    news = await fetch_lookonchain_news(limit=1)
    assert isinstance(news, list)
    assert len(news) == 1
    assert news[0]["title"] == "Test Lookonchain News"
    assert news[0]["source"] == "Lookonchain" 