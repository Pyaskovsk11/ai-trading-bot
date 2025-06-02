from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class TradeSide(str, Enum):
    """
    Сторона торговой сделки.
    """
    BUY = "BUY"
    SELL = "SELL"

class TradeStatus(str, Enum):
    """
    Статус торговой сделки.
    """
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class TradeCreate(BaseModel):
    """
    Схема для создания новой торговой сделки.
    """
    symbol: str = Field(..., description="Торговый символ (например, BTCUSDT)")
    side: TradeSide = Field(..., description="Сторона сделки (BUY/SELL)")
    quantity: float = Field(..., description="Количество для торговли")
    leverage: int = Field(1, description="Кредитное плечо")
    stop_loss: Optional[float] = Field(None, description="Уровень стоп-лосса")
    take_profit: Optional[float] = Field(None, description="Уровень тейк-профита")

class TradeResponse(TradeCreate):
    """
    Схема для ответа с информацией о торговой сделке.
    """
    id: int = Field(..., description="ID сделки")
    status: TradeStatus = Field(..., description="Статус сделки")
    entry_price: float = Field(..., description="Цена входа")
    exit_price: Optional[float] = Field(None, description="Цена выхода")
    pnl: Optional[float] = Field(None, description="Прибыль/убыток")
    created_at: datetime = Field(..., description="Время создания сделки")
    closed_at: Optional[datetime] = Field(None, description="Время закрытия сделки")

    class Config:
        from_attributes = True 