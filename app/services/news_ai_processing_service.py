import logging
from sqlalchemy.orm import Session
from app.db.models import NewsArticle
from app.services.sentiment_service import SentimentService
from app.services.ner_service import NERService
from app.services.news_relevance_service import NewsRelevanceService
from app.services.rag_analysis_service import RAGAnalysisService
from typing import Optional

logger = logging.getLogger(__name__)

class NewsAIProcessingService:
    """
    Сервис для полной AI-обработки новости: sentiment, NER, relevance, RAG.
    Использует асинхронные AI-сервисы через DI.
    """
    def __init__(
        self,
        db: Session,
        sentiment_service: SentimentService,
        ner_service: NERService,
        relevance_service: NewsRelevanceService,
        rag_service: RAGAnalysisService
    ):
        self.db = db
        self.sentiment_service = sentiment_service
        self.ner_service = ner_service
        self.relevance_service = relevance_service
        self.rag_service = rag_service

    async def process_news(self, news_id: int) -> Optional[NewsArticle]:
        news = self.db.query(NewsArticle).filter(NewsArticle.id == news_id).first()
        if not news:
            logger.error(f"NewsArticle id={news_id} not found")
            return None
        try:
            # Sentiment
            sentiment = await self.sentiment_service.analyze_sentiment(news.content)
            news.sentiment_score = sentiment.get("sentiment_score") if sentiment else None
            # NER
            entities = await self.ner_service.extract_entities(news.content)
            if hasattr(news, "extracted_entities") and entities:
                news.extracted_entities = entities.get("entities")
            # Relevance
            assets = news.affected_assets if hasattr(news, "affected_assets") and news.affected_assets else []
            relevance = await self.relevance_service.assess_relevance(news.content, assets)
            if hasattr(news, "relevance_score") and relevance:
                news.relevance_score = relevance.get("relevance_score")
            # RAG (summary, XAI)
            rag = await self.rag_service.analyze(news.content)
            if rag:
                if hasattr(news, "summary"):
                    news.summary = rag.get("summary")
                if hasattr(news, "xai_explanation"):
                    news.xai_explanation = rag.get("xai_explanation")
            self.db.commit()
            logger.info(f"AI processing complete for news id={news_id}")
            return news
        except Exception as e:
            logger.error(f"[NewsAIProcessingService] Error processing news id={news_id}: {e}")
            self.db.rollback()
            return None 