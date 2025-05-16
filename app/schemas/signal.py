from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime

class XAIExplanationBase(BaseModel):
    """
    Базовая модель XAI объяснения для сигнала.
    """
    explanation_text: str
    factors_used: Dict[str, float]
    model_version: Optional[str] = None

class NewsBase(BaseModel):
    """
    Базовая модель новости для вложения в сигнал.
    """
    title: str
    source: str
    published_at: datetime
    sentiment_score: float
    url: Optional[str] = None

    @validator('sentiment_score')
    def validate_sentiment_score(cls, v):
        if not -1 <= v <= 1:
            raise ValueError('Sentiment score must be between -1 and 1')
        return v

class NewsRelevance(BaseModel):
    """
    Модель связи новости с сигналом и оценки релевантности.
    """
    news: NewsBase
    relevance_score: float = Field(..., ge=0, le=1)
    impact_type: str

    @validator('impact_type')
    def validate_impact_type(cls, v):
        allowed_types = ["POSITIVE", "NEGATIVE", "NEUTRAL"]
        if v not in allowed_types:
            raise ValueError(f'Impact type must be one of {allowed_types}')
        return v

class SignalBase(BaseModel):
    """
    Базовая модель сигнала для создания и чтения.
    """
    asset_pair: str
    signal_type: str
    confidence_score: float = Field(..., ge=0, le=1)
    price_at_signal: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    time_frame: str
    expires_at: Optional[datetime] = None
    technical_indicators: Dict[str, float]
    smart_money_influence: Optional[float] = None
    volatility_estimate: Optional[float] = None

    @validator('signal_type')
    def validate_signal_type(cls, v):
        allowed_types = ["BUY", "SELL", "HOLD"]
        if v not in allowed_types:
            raise ValueError(f'Signal type must be one of {allowed_types}')
        return v

    @validator('time_frame')
    def validate_time_frame(cls, v):
        allowed_frames = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        if v not in allowed_frames:
            raise ValueError(f'Time frame must be one of {allowed_frames}')
        return v

    @validator('smart_money_influence')
    def validate_smart_money_influence(cls, v):
        if v is not None and not -1 <= v <= 1:
            raise ValueError('Smart money influence must be between -1 and 1')
        return v

class SignalCreate(SignalBase):
    """
    Модель для создания нового сигнала.
    """
    xai_explanation: Optional[XAIExplanationBase] = None
    related_news: Optional[List[NewsRelevance]] = None

class SignalRead(SignalBase):
    """
    Модель для базового чтения сигнала.
    """
    id: int
    created_at: datetime
    status: str
    xai_explanation_id: Optional[int] = None

    class Config:
        orm_mode = True

class SignalDetailsRead(SignalRead):
    """
    Расширенная модель для детального чтения сигнала.
    """
    xai_explanation: Optional[XAIExplanationBase] = None
    related_news: List[NewsRelevance] = []
    trades_count: int
    success_rate: Optional[float] = None

    class Config:
        orm_mode = True

class SignalUpdate(BaseModel):
    """
    Модель для обновления существующего сигнала.
    """
    status: Optional[str] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    expires_at: Optional[datetime] = None

    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed_status = ["ACTIVE", "EXPIRED", "TRIGGERED", "CANCELLED"]
            if v not in allowed_status:
                raise ValueError(f'Status must be one of {allowed_status}')
        return v

class SignalList(BaseModel):
    """
    Модель для возврата списка сигналов с пагинацией.
    """
    items: List[SignalRead]
    total: int
    page: int
    size: int
    pages: int 