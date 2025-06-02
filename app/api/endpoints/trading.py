from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.exchange_service import BingXExchangeService
from app.core.config import settings
from app.schemas.trading import TradeCreate, TradeResponse
from app.services.trading import TradingService
from app.core.exceptions import ExchangeError, RateLimitError

router = APIRouter()

@router.get("/account/balance", response_model=Dict[str, float])
def get_account_balance(db: Session = Depends(get_db)):
    """
    Получить баланс аккаунта
    """
    exchange_service = BingXExchangeService(is_demo=settings.USE_DEMO_ACCOUNT)
    try:
        return exchange_service.get_account_balance()
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail={"detail": str(e), "code": "rate_limit"})
    except ExchangeError as e:
        raise HTTPException(status_code=400, detail={"detail": str(e), "code": "exchange_error"})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"detail": "Internal server error", "code": "internal_error"})

@router.get("/account/positions", response_model=List[Dict[str, Any]])
def get_open_positions(db: Session = Depends(get_db)):
    """
    Получить открытые позиции на бирже
    """
    exchange_service = BingXExchangeService(is_demo=settings.USE_DEMO_ACCOUNT)
    return exchange_service.get_open_positions()

@router.post("/orders/market")
def place_market_order(
    symbol: str,
    side: str,
    quantity: float,
    db: Session = Depends(get_db)
):
    """
    Разместить рыночный ордер
    """
    if side not in ['BUY', 'SELL']:
        raise HTTPException(status_code=400, detail={"detail": "Invalid order side. Must be 'BUY' or 'SELL'", "code": "validation_error"})
    exchange_service = BingXExchangeService(is_demo=settings.USE_DEMO_ACCOUNT)
    try:
        return exchange_service.place_market_order(symbol, side, quantity)
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail={"detail": str(e), "code": "rate_limit"})
    except ExchangeError as e:
        raise HTTPException(status_code=400, detail={"detail": str(e), "code": "exchange_error"})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"detail": "Internal server error", "code": "internal_error"})

@router.post("/trades/", response_model=TradeResponse)
def create_trade(
    trade: TradeCreate,
    db: Session = Depends(get_db)
) -> TradeResponse:
    """
    Создает новую торговую сделку.
    """
    trading_service = TradingService(db)
    return trading_service.create_trade(trade)

@router.get("/trades/", response_model=List[TradeResponse])
def get_trades(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[TradeResponse]:
    """
    Получает список всех торговых сделок.
    """
    trading_service = TradingService(db)
    return trading_service.get_trades(skip=skip, limit=limit)

@router.get("/trades/{trade_id}", response_model=TradeResponse)
def get_trade(
    trade_id: int,
    db: Session = Depends(get_db)
) -> TradeResponse:
    """
    Получает информацию о конкретной торговой сделке.
    """
    trading_service = TradingService(db)
    trade = trading_service.get_trade(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade 