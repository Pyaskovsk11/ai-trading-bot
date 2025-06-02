from fastapi import APIRouter
from app.api.endpoints import signals, users, news, trading

api_router = APIRouter()
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(trading.router, prefix="/trading", tags=["trading"]) 