from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import logging
from app.db.session import get_db
from app.schemas.trade import TradeCreate, TradeRead, TradeUpdate, TradeList
from app.services import trade_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trades", tags=["Trades"])

@router.get("/", response_model=TradeList)
def list_trades(
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(100, ge=1, le=500, description="Максимум записей на страницу"),
    db: Session = Depends(get_db)
) -> TradeList:
    """
    Получить список сделок с пагинацией.
    """
    items, total = trade_service.get_trades(db, skip=skip, limit=limit)
    page = (skip // limit) + 1 if limit else 1
    pages = (total + limit - 1) // limit if limit else 1
    return TradeList(items=items, total=total, page=page, size=limit, pages=pages)

@router.get("/{trade_id}", response_model=TradeRead)
def get_trade(trade_id: int, db: Session = Depends(get_db)) -> TradeRead:
    """
    Получить сделку по ID.
    """
    trade = trade_service.get_trade_by_id(db, trade_id)
    if not trade:
        logger.warning(f"Trade {trade_id} not found.")
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade

@router.post("/", response_model=TradeRead, status_code=status.HTTP_201_CREATED)
def create_trade(trade_in: TradeCreate, db: Session = Depends(get_db)) -> TradeRead:
    """
    Создать новую сделку.
    """
    trade = trade_service.create_trade(db, trade_in)
    return trade

@router.put("/{trade_id}", response_model=TradeRead)
def update_trade(trade_id: int, trade_in: TradeUpdate, db: Session = Depends(get_db)) -> TradeRead:
    """
    Обновить сделку по ID.
    """
    trade = trade_service.update_trade(db, trade_id, trade_in)
    if not trade:
        logger.warning(f"Trade {trade_id} not found for update.")
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade

@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trade(trade_id: int, db: Session = Depends(get_db)) -> None:
    """
    Удалить сделку по ID.
    """
    success = trade_service.delete_trade(db, trade_id)
    if not success:
        logger.warning(f"Trade {trade_id} not found for delete.")
        raise HTTPException(status_code=404, detail="Trade not found") 