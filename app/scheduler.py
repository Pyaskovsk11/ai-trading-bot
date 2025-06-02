import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.news_parser_service import fetch_and_save_all_news
from app.services.news_ai_processing_service import NewsAIProcessingService
from app.services.signal_ai_modifier_service import SignalAIModifierService
from typing import Any
import app.services.sentiment_service
import app.services.ner_service
import app.services.news_relevance_service
import app.services.rag_analysis_service
from app.services.ai_api_client import AIAPIClient

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

def get_db() -> Session:
    """
    Получить новую сессию базы данных.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def start_scheduler() -> None:
    """
    Запускает APScheduler и регистрирует периодические задачи.
    """
    scheduler.add_job(parse_news_job, IntervalTrigger(minutes=5), id="parse_news")
    scheduler.add_job(ai_process_news_job, IntervalTrigger(minutes=7), id="ai_process_news")
    scheduler.add_job(update_signals_job, IntervalTrigger(minutes=10), id="update_signals")
    scheduler.start()
    logger.info("Scheduler started with jobs: parse_news, ai_process_news, update_signals")

async def parse_news_job() -> None:
    """
    Периодически парсит новости со всех источников.
    """
    logger.info("[Scheduler] Запуск парсинга новостей...")
    db = SessionLocal()
    try:
        await fetch_and_save_all_news(db)
    finally:
        db.close()

async def ai_process_news_job() -> None:
    """
    Периодически запускает AI-обработку новых новостей.
    """
    logger.info("[Scheduler] Запуск AI-обработки новостей...")
    db = SessionLocal()
    try:
        service = NewsAIProcessingService(
            db,
            app.services.sentiment_service.SentimentService(AIAPIClient("http://localhost:8000")),
            app.services.ner_service.NERService(AIAPIClient("http://localhost:8000")),
            app.services.news_relevance_service.NewsRelevanceService(),
            app.services.rag_analysis_service.RAGAnalysisService(app.services.rag_analysis_service.AIAPIClient("http://localhost:8000"))
        )
        # Здесь можно реализовать обработку всех не обработанных новостей
        # Например, пройтись по всем news, где processed=False
        # await service.process_all_unprocessed_news()
    finally:
        db.close()

async def update_signals_job() -> None:
    """
    Периодически обновляет confidence сигналов на основе новостей.
    """
    logger.info("[Scheduler] Запуск обновления confidence сигналов...")
    db = SessionLocal()
    try:
        service = SignalAIModifierService(db)
        await service.update_all_signals_confidence()
    finally:
        db.close() 