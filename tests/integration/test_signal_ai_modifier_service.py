import pytest
from sqlalchemy.orm import Session
from app.db.models import Signal, NewsArticle
from app.services.signal_ai_modifier_service import SignalAIModifierService
from datetime import datetime

@pytest.mark.asyncio
async def test_signal_ai_modifier_integration(db_session: Session):
    # Добавляем сигнал и новость
    signal = Signal(asset_pair="ETH/USDT", confidence=0.6, confidence_score=0.6, price_at_signal=3500, time_frame="1h", status="NEW", created_at=datetime.utcnow(), signal_type="AI")
    db_session.add(signal)
    db_session.commit()
    news = NewsArticle(
        title="ETH positive",
        content="ETH upgrade successful",
        source="Test",
        published_at=datetime.utcnow(),
        fetched_at=datetime.utcnow(),
        sentiment_score=0.7
    )
    db_session.add(news)
    db_session.commit()

    service = SignalAIModifierService(db_session)
    updated_signal = service.modify_signal_confidence(signal.id)
    assert updated_signal is not None
    assert updated_signal.ai_confidence_modifier == pytest.approx(0.7) 