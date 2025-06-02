import logging
from typing import Optional, List, Dict
from app.services.ai_api_client import AIAPIClient

logger = logging.getLogger(__name__)

class NERService:
    """
    Сервис для извлечения сущностей из текста через внешний AI API.
    Поддерживает одиночный и пакетный анализ, in-memory кэширование.
    """
    def __init__(self, ai_client: AIAPIClient, enable_cache: bool = True):
        self.ai_client = ai_client
        self.enable_cache = enable_cache
        self._cache: Dict[int, Dict] = {} if enable_cache else None

    async def extract_entities(self, text: str) -> Optional[Dict]:
        """
        Извлекает сущности из одного текста.
        :param text: текст для анализа
        :return: dict с entities или None при ошибке
        """
        text_hash = hash(text)
        if self.enable_cache and text_hash in self._cache:
            logger.info("[NERService] Cache hit for text")
            return self._cache[text_hash]
        try:
            response = await self.ai_client.post('/ner', {"text": text})
            result = {
                "entities": response.get("entities", [])
            }
            if self.enable_cache:
                self._cache[text_hash] = result
            return result
        except Exception as e:
            logger.error(f"[NERService] Error extracting entities: {e}")
            return None

    async def extract_batch(self, texts: List[str]) -> List[Optional[Dict]]:
        """
        Пакетное извлечение сущностей.
        :param texts: список текстов
        :return: список dict с результатами для каждого текста
        """
        results: List[Optional[Dict]] = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []
        for i, text in enumerate(texts):
            text_hash = hash(text)
            if self.enable_cache and text_hash in self._cache:
                results[i] = self._cache[text_hash]
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)
        if uncached_texts:
            try:
                response = await self.ai_client.post('/ner/batch', {"texts": uncached_texts})
                batch_results = response.get("results", [])
                for idx, res in zip(uncached_indices, batch_results):
                    result = {
                        "entities": res.get("entities", [])
                    }
                    results[idx] = result
                    if self.enable_cache:
                        self._cache[hash(texts[idx])] = result
            except Exception as e:
                logger.error(f"[NERService] Error in batch NER: {e}")
        return results 