import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.models import Trade
from app.schemas.trade import TradeCreate, TradeUpdate
from datetime import datetime

logger = logging.getLogger(__name__)

def get_trades(db: Session, skip: int = 0, limit: int = 100) -> Tuple[List[Trade], int]:
    """
    Получить список сделок с пагинацией.
    """
    try:
        query = db.query(Trade)
        total = query.count()
        items = query.order_by(Trade.entry_time.desc()).offset(skip).limit(limit).all()
        return items, total
    except SQLAlchemyError as e:
        logger.error(f"Error fetching trades: {e}")
        return [], 0

def get_trade_by_id(db: Session, trade_id: int) -> Optional[Trade]:
    """
    Получить сделку по ID.
    """
    return db.query(Trade).filter(Trade.id == trade_id).first()

def create_trade(db: Session, trade_in: TradeCreate) -> Optional[Trade]:
    """
    Создать новую сделку.
    """
    if trade_in.volume is not None and trade_in.volume <= 0:
        logger.error("Trade volume must be positive")
        return None
    try:
        db_trade = Trade(
            signal_id=trade_in.signal_id,
            user_id=trade_in.user_id,
            entry_price=trade_in.entry_price,
            exit_price=trade_in.exit_price,
            volume=trade_in.volume,
            pnl=trade_in.pnl,
            pnl_percentage=trade_in.pnl_percentage,
            entry_time=trade_in.entry_time or datetime.utcnow(),
            exit_time=trade_in.exit_time,
            status=trade_in.status,
            notes=trade_in.notes,
        )
        db.add(db_trade)
        db.commit()
        db.refresh(db_trade)
        return db_trade
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating trade: {e}")
        return None

def update_trade(db: Session, trade_id: int, trade_in: TradeUpdate) -> Optional[Trade]:
    """
    Обновить сделку по ID.
    """
    db_trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not db_trade:
        return None
    try:
        for field, value in trade_in.dict(exclude_unset=True).items():
            setattr(db_trade, field, value)
        db.commit()
        db.refresh(db_trade)
        return db_trade
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating trade: {e}")
        return None

def delete_trade(db: Session, trade_id: int) -> bool:
    """
    Удалить сделку по ID.
    """
    db_trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not db_trade:
        return False
    try:
        db.delete(db_trade)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting trade: {e}")
        return False 