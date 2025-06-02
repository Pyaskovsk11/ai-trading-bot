import httpx
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class AIAPIClient:
    """
    Асинхронный клиент для вызова внешних AI endpoint'ов (Sentiment, NER, Relevance, Summarization и др.).
    """
    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Асинхронно отправляет POST-запрос к AI endpoint.
        :param endpoint: относительный путь (например, /sentiment)
        :param payload: тело запроса (dict)
        :return: ответ API (dict)
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"[AIAPIClient] POST {url} OK")
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"[AIAPIClient] HTTP error {e.response.status_code} for {url}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"[AIAPIClient] Error calling {url}: {e}")
            raise 