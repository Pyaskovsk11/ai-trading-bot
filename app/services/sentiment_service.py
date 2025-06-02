import logging
from typing import Optional, List, Dict
from app.services.ai_api_client import AIAPIClient

logger = logging.getLogger(__name__)

class SentimentService:
    """
    Сервис для анализа тональности текста через внешний AI API.
    Поддерживает одиночный и пакетный анализ, in-memory кэширование.
    """
    def __init__(self, ai_client: AIAPIClient, enable_cache: bool = True):
        self.ai_client = ai_client
        self.enable_cache = enable_cache
        self._cache: Dict[int, Dict] = {} if enable_cache else None

    async def analyze_sentiment(self, text: str) -> Optional[Dict]:
        """
        Анализ тональности одного текста.
        :param text: текст для анализа
        :return: dict с sentiment_score, label и др. или None при ошибке
        """
        text_hash = hash(text)
        if self.enable_cache and text_hash in self._cache:
            logger.info("[SentimentService] Cache hit for text")
            return self._cache[text_hash]
        try:
            response = await self.ai_client.post('/sentiment', {"text": text})
            result = {
                "sentiment_score": response.get("sentiment_score"),
                "label": response.get("label"),
                "confidence": response.get("confidence")
            }
            if self.enable_cache:
                self._cache[text_hash] = result
            return result
        except Exception as e:
            logger.error(f"[SentimentService] Error analyzing sentiment: {e}")
            return None

    async def analyze_batch(self, texts: List[str]) -> List[Optional[Dict]]:
        """
        Пакетный анализ тональности.
        :param texts: список текстов
        :return: список dict с результатами для каждого текста
        """
        results: List[Optional[Dict]] = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []
        # Проверяем кэш
        for i, text in enumerate(texts):
            text_hash = hash(text)
            if self.enable_cache and text_hash in self._cache:
                results[i] = self._cache[text_hash]
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)
        # Запрашиваем только не кэшированные
        if uncached_texts:
            try:
                response = await self.ai_client.post('/sentiment/batch', {"texts": uncached_texts})
                batch_results = response.get("results", [])
                for idx, res in zip(uncached_indices, batch_results):
                    result = {
                        "sentiment_score": res.get("sentiment_score"),
                        "label": res.get("label"),
                        "confidence": res.get("confidence")
                    }
                    results[idx] = result
                    if self.enable_cache:
                        self._cache[hash(texts[idx])] = result
            except Exception as e:
                logger.error(f"[SentimentService] Error in batch sentiment: {e}")
        return results 