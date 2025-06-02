import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api import signals, users, news, trades, deep_learning, adaptive_trading
from app.api.endpoints import coins
from app.api.v1 import strategy, backtest
from app.utils.scheduler import start_scheduler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Futures Trading Bot")

# CORS: разрешить все источники (для разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"])
def read_root() -> dict:
    """
    Базовый эндпоинт для проверки работоспособности API.
    """
    logger.info("Health check endpoint called.")
    return {"status": "ok", "message": "AI Trading Bot backend is running."}

# from app.api import users, signals, trades  # Пример для будущих роутеров
# app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(signals.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(news.router, prefix="/api/v1/news", tags=["News"])
app.include_router(trades.router, prefix="/api/v1")
app.include_router(deep_learning.router, prefix="/api/v1")
app.include_router(adaptive_trading.router, prefix="/api/v1")
app.include_router(strategy.router, prefix="/api/v1")
app.include_router(backtest.router, prefix="/api/v1")
app.include_router(coins.router, prefix="/api/v1/coins", tags=["Coins"])
# app.include_router(trades.router, prefix="/api/v1/trades", tags=["Trades"])

start_scheduler() 