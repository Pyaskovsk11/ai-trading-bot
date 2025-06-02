from pydantic import BaseModel
from typing import Optional

class SignalNewsRelevanceCreate(BaseModel):
    signal_id: int
    news_id: int
    relevance_score: float
    impact_type: str

class SignalNewsRelevanceOut(SignalNewsRelevanceCreate):
    id: int

    class Config:
        orm_mode = True 