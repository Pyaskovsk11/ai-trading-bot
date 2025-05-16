from pydantic import BaseModel, Field, validator, AnyUrl
from typing import Optional, List
from datetime import datetime

class NewsBase(BaseModel):
    title: str
    content: str
    source: Optional[str] = None
    published_at: datetime
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    url: Optional[AnyUrl] = None
    affected_assets: Optional[List[str]] = None

    @validator('sentiment_score')
    def validate_sentiment_score(cls, v):
        if v is not None and not -1 <= v <= 1:
            raise ValueError('Sentiment score must be between -1 and 1')
        return v

class NewsCreate(NewsBase):
    fetched_at: Optional[datetime] = None
    processed: Optional[bool] = False

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: Optional[datetime] = None
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    processed: Optional[bool] = None
    url: Optional[AnyUrl] = None
    affected_assets: Optional[List[str]] = None

class NewsRead(NewsBase):
    id: int
    fetched_at: datetime
    processed: bool

    class Config:
        orm_mode = True

class NewsList(BaseModel):
    items: List[NewsRead]
    total: int
    page: int
    size: int
    pages: int 