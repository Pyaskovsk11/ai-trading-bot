import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.models import Signal
from app.schemas.signal import SignalCreate, SignalUpdate

logger = logging.getLogger(__name__)


def get_signals(db: Session, skip: int = 0, limit: int = 100) -> Tuple[List[Signal], int]:
    """
    Получить список сигналов с пагинацией.
    """
    try:
        query = db.query(Signal)
        total = query.count()
        items = query.order_by(Signal.created_at.desc()).offset(skip).limit(limit).all()
        return items, total
    except SQLAlchemyError as e:
        logger.error(f"Error fetching signals: {e}")
        return [], 0

def get_signal_by_id(db: Session, signal_id: int) -> Optional[Signal]:
    """
    Получить сигнал по ID.
    """
    return db.query(Signal).filter(Signal.id == signal_id).first()

def create_signal(db: Session, signal_in: SignalCreate) -> Optional[Signal]:
    """
    Создать новый сигнал.
    """
    if signal_in.confidence_score is not None and not 0 <= signal_in.confidence_score <= 1:
        logger.error("Confidence score must be between 0 and 1")
        return None
    try:
        db_signal = Signal(
            asset_pair=signal_in.asset_pair,
            signal_type=signal_in.signal_type,
            confidence_score=signal_in.confidence_score,
            price_at_signal=signal_in.price_at_signal,
            target_price=signal_in.target_price,
            stop_loss=signal_in.stop_loss,
            time_frame=signal_in.time_frame,
            expires_at=signal_in.expires_at,
            technical_indicators=signal_in.technical_indicators,
            smart_money_influence=signal_in.smart_money_influence,
            volatility_estimate=signal_in.volatility_estimate,
            status="ACTIVE",
        )
        db.add(db_signal)
        db.commit()
        db.refresh(db_signal)
        return db_signal
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating signal: {e}")
        return None

def update_signal(db: Session, signal_id: int, signal_in: SignalUpdate) -> Optional[Signal]:
    """
    Обновить существующий сигнал.
    """
    db_signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not db_signal:
        return None
    try:
        for field, value in signal_in.dict(exclude_unset=True).items():
            setattr(db_signal, field, value)
        db.commit()
        db.refresh(db_signal)
        return db_signal
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating signal: {e}")
        return None

def delete_signal(db: Session, signal_id: int) -> bool:
    """
    Удалить сигнал по ID.
    """
    db_signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not db_signal:
        return False
    try:
        db.delete(db_signal)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting signal: {e}")
        return False 