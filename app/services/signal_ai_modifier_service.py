import logging
from sqlalchemy.orm import Session
from app.db.models import Signal, NewsArticle
from typing import Optional
from datetime import datetime, timedelta, UTC

logger = logging.getLogger(__name__)

class SignalAIModifierService:
    """
    Сервис для корректировки confidence сигнала на основе новостей.
    """
    def __init__(self, db: Session):
        self.db = db

    def modify_signal_confidence(self, signal_id: int) -> Optional[Signal]:
        signal = self.db.query(Signal).filter(Signal.id == signal_id).first()
        if not signal:
            logger.error(f"Signal id={signal_id} not found")
            return None

        # Находим релевантные новости за последние 24 часа
        time_threshold = datetime.now(UTC) - timedelta(hours=24)
        news = (
            self.db.query(NewsArticle)
            .filter(
                NewsArticle.sentiment_score != None,
                NewsArticle.published_at >= time_threshold
            )
            .order_by(NewsArticle.published_at.desc())
            .limit(5)  # Увеличиваем лимит для лучшего усреднения
            .all()
        )

        if not news:
            logger.info(f"No relevant news found for signal {signal_id}")
            return signal

        # Рассчитываем средний sentiment
        sentiment_scores = [n.sentiment_score for n in news if n.sentiment_score is not None]
        if not sentiment_scores:
            return signal

        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        
        # Нормализуем модификатор в диапазон [-0.2, 0.2]
        modifier = max(min(avg_sentiment * 0.2, 0.2), -0.2)
        
        signal.ai_confidence_modifier = modifier
        self.db.commit()
        logger.info(f"Signal id={signal_id} confidence modified by {modifier}")
        return signal

    async def update_all_signals_confidence(self) -> None:
        """
        Асинхронно обновляет confidence всех сигналов на основе новостей.
        """
        signals = self.db.query(Signal).all()
        logger.info(f"[Scheduler] Обновление confidence для {len(signals)} сигналов...")
        for signal in signals:
            self.modify_signal_confidence(signal.id)
        logger.info("[Scheduler] Обновление confidence сигналов завершено.") 