import logging
from typing import List, Dict, Any
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

ARKHAM_URL = "https://intel.arkm.com/"

async def fetch_arkham_news(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Асинхронно парсит последние новости/события с Arkham.
    Возвращает список словарей с ключами: title, content, source, published_at, url, sentiment_score.
    """
    news_list = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(ARKHAM_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            # Пример: парсим карточки новостей (заменить на актуальный CSS-селектор)
            for item in soup.select(".css-1q1h6c7")[:limit]:
                title = item.get_text(strip=True)
                url = ARKHAM_URL  # Можно доработать для получения конкретной ссылки
                news_list.append({
                    "title": title,
                    "content": title,
                    "source": "Arkham",
                    "published_at": datetime.utcnow(),
                    "url": url,
                    "sentiment_score": 0.0
                })
        logger.info(f"[Arkham] Parsed {len(news_list)} news items.")
    except Exception as e:
        logger.error(f"[Arkham] Error fetching news: {e}")
    return news_list 