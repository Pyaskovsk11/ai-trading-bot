from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Trade
from app.schemas.trading import TradeCreate, TradeResponse
from app.core.config import settings

class TradingService:
    """
    Сервис для работы с торговыми операциями.
    """
    def __init__(self, db: Session):
        self.db = db

    def create_trade(self, trade: TradeCreate) -> TradeResponse:
        """
        Создает новую торговую сделку.
        """
        db_trade = Trade(
            symbol=trade.symbol,
            side=trade.side,
            quantity=trade.quantity,
            leverage=trade.leverage,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit,
            status="OPEN",
            created_at=datetime.utcnow()
        )
        self.db.add(db_trade)
        self.db.commit()
        self.db.refresh(db_trade)
        return db_trade

    def get_trades(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[TradeResponse]:
        """
        Получает список всех торговых сделок.
        """
        return self.db.query(Trade).offset(skip).limit(limit).all()

    def get_trade(self, trade_id: int) -> Optional[TradeResponse]:
        """
        Получает информацию о конкретной торговой сделке.
        """
        return self.db.query(Trade).filter(Trade.id == trade_id).first()

    def close_trade(
        self,
        trade_id: int,
        exit_price: float
    ) -> Optional[TradeResponse]:
        """
        Закрывает торговую сделку.
        """
        trade = self.get_trade(trade_id)
        if not trade:
            return None

        trade.status = "CLOSED"
        trade.exit_price = exit_price
        trade.closed_at = datetime.utcnow()
        
        # Расчет P&L
        if trade.side == "BUY":
            trade.pnl = (exit_price - trade.entry_price) * trade.quantity
        else:
            trade.pnl = (trade.entry_price - exit_price) * trade.quantity

        self.db.commit()
        self.db.refresh(trade)
        return trade 