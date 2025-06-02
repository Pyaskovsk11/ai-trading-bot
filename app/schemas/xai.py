from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class XAIExplanationCreate(BaseModel):
    explanation_text: str
    factors_used: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None

class XAIExplanationOut(XAIExplanationCreate):
    id: int
    created_at: Optional[str] = None

    class Config:
        orm_mode = True 