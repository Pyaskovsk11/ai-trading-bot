import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class NewsRelevanceService:
    """
    Сервис для оценки релевантности новости к активам/темам.
    """
    def __init__(self, ai_client: Optional[object] = None):
        self.ai_client = ai_client

    async def assess_relevance(self, text: str, assets: List[str]) -> Dict[str, Any]:
        """
        Оценивает релевантность текста к списку активов.
        Возвращает словарь с relevance_score.
        """
        if self.ai_client:
            try:
                response = await self.ai_client.post("/relevance", {"text": text, "assets": assets})
                return response
            except Exception as e:
                logger.error(f"[NewsRelevanceService] Error in assess_relevance: {e}")
                return None
        logger.info("Relevance assessment called (stub)")
        return {"relevance_score": 0.5}

    async def assess_batch(self, texts: List[str], assets: List[str]) -> List[Optional[Dict[str, Any]]]:
        """
        Пакетная оценка релевантности.
        """
        if self.ai_client:
            try:
                response = await self.ai_client.post("/relevance/batch", {"texts": texts, "assets": assets})
                return response.get("results", [])
            except Exception as e:
                logger.error(f"[NewsRelevanceService] Error in assess_batch: {e}")
                return [None] * len(texts)
        logger.info("Batch relevance assessment called (stub)")
        return [{"relevance_score": 0.5}] * len(texts) 