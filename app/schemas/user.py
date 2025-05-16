from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    telegram_id: str = Field(..., max_length=50)
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    whitelist_status: bool = False
    settings: Optional[Dict[str, Any]] = None

    @validator('telegram_id')
    def validate_telegram_id(cls, v):
        if not v or not v.strip():
            raise ValueError('telegram_id must not be empty')
        return v

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    whitelist_status: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None

class UserRead(UserBase):
    id: int
    created_at: datetime
    last_active: Optional[datetime] = None

    class Config:
        orm_mode = True

class UserList(BaseModel):
    items: List[UserRead]
    total: int
    page: int
    size: int
    pages: int 