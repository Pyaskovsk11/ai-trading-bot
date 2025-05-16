import logging
import os
from typing import Dict, Any
import requests

logger = logging.getLogger(__name__)

RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8001/api")
RAG_API_KEY = os.getenv("RAG_API_KEY")
TIMEOUT = 10

def analyze_news_with_hector_rag(news_text: str) -> Dict[str, Any]:
    """
    Анализ новости через Hector RAG (реальный запрос).
    Возвращает затронутые активы, оценку тональности и краткое содержание.
    """
    try:
        headers = {"Authorization": f"Bearer {RAG_API_KEY}"} if RAG_API_KEY else {}
        payload = {"text": news_text}
        resp = requests.post(RAG_API_URL, headers=headers, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return {
            "affected_assets": data.get("affected_assets", []),
            "sentiment_score": data.get("sentiment_score", 0.0),
            "summary": data.get("summary", "")
        }
    except Exception as e:
        logger.error(f"Error analyzing news with RAG: {e}")
        return {
            "affected_assets": [],
            "sentiment_score": 0.0,
            "summary": "Не удалось получить анализ новости."
        } 