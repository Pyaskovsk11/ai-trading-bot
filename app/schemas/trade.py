from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TradeBase(BaseModel):
    signal_id: Optional[int] = None
    user_id: Optional[int] = None
    entry_price: float
    exit_price: Optional[float] = None
    volume: float
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    status: str
    notes: Optional[str] = None

class TradeCreate(TradeBase):
    pass

class TradeUpdate(BaseModel):
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None
    exit_time: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class TradeRead(TradeBase):
    id: int
    entry_time: datetime

    class Config:
        orm_mode = True

class TradeList(BaseModel):
    items: List[TradeRead]
    total: int
    page: int
    size: int
    pages: int 