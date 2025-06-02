import pytest
from sqlalchemy.orm import Session
from app.db.models import Signal, NewsArticle
from app.services.signal_ai_modifier_service import SignalAIModifierService
from datetime import datetime, timedelta, UTC

def test_modify_signal_confidence(db_session: Session):
    # Создаем сигнал
    signal = Signal(
        asset_pair="BTC/USDT",
        confidence=0.5,
        confidence_score=0.5,
        price_at_signal=50000,
        time_frame="1h",
        status="NEW",
        created_at=datetime.now(UTC),
        signal_type="AI"
    )
    db_session.add(signal)
    db_session.commit()

    # Создаем новости с разными sentiment scores
    now = datetime.now(UTC)
    news = [
        NewsArticle(
            title="Very bullish news",
            content="BTC to the moon!",
            source="Test",
            published_at=now - timedelta(hours=1),
            fetched_at=now - timedelta(hours=1),
            sentiment_score=0.9
        ),
        NewsArticle(
            title="Slightly bearish news",
            content="BTC might dip",
            source="Test",
            published_at=now - timedelta(hours=2),
            fetched_at=now - timedelta(hours=2),
            sentiment_score=-0.3
        ),
        NewsArticle(
            title="Neutral news",
            content="BTC stable",
            source="Test",
            published_at=now - timedelta(hours=3),
            fetched_at=now - timedelta(hours=3),
            sentiment_score=0.1
        )
    ]
    db_session.add_all(news)
    db_session.commit()

    # Запускаем сервис
    service = SignalAIModifierService(db_session)
    updated_signal = service.modify_signal_confidence(signal.id)

    # Проверяем результаты
    assert updated_signal is not None
    assert updated_signal.ai_confidence_modifier is not None
    
    # Проверяем, что модификатор находится в допустимом диапазоне
    assert -0.2 <= updated_signal.ai_confidence_modifier <= 0.2
    
    # Проверяем, что модификатор примерно соответствует ожидаемому значению
    expected_modifier = (0.9 + -0.3 + 0.1) / 3 * 0.2  # Среднее * 0.2 для нормализации
    assert abs(updated_signal.ai_confidence_modifier - expected_modifier) < 0.01 