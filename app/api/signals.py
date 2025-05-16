from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import logging
from app.db.session import get_db
from app.schemas.signal import SignalCreate, SignalRead, SignalUpdate, SignalList
from app.services import signal_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/signals", tags=["Signals"])

@router.get("/", response_model=SignalList)
def list_signals(
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(100, ge=1, le=500, description="Максимум записей на страницу"),
    db: Session = Depends(get_db)
) -> SignalList:
    """
    Получить список торговых сигналов с пагинацией.
    """
    items, total = signal_service.get_signals(db, skip=skip, limit=limit)
    page = (skip // limit) + 1 if limit else 1
    pages = (total + limit - 1) // limit if limit else 1
    return SignalList(items=items, total=total, page=page, size=limit, pages=pages)

@router.get("/{signal_id}", response_model=SignalRead)
def get_signal(signal_id: int, db: Session = Depends(get_db)) -> SignalRead:
    """
    Получить сигнал по ID.
    """
    signal = signal_service.get_signal_by_id(db, signal_id)
    if not signal:
        logger.warning(f"Signal {signal_id} not found.")
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal

@router.post("/", response_model=SignalRead, status_code=status.HTTP_201_CREATED)
def create_signal(signal_in: SignalCreate, db: Session = Depends(get_db)) -> SignalRead:
    """
    Создать новый торговый сигнал.
    """
    signal = signal_service.create_signal(db, signal_in)
    return signal

@router.put("/{signal_id}", response_model=SignalRead)
def update_signal(signal_id: int, signal_in: SignalUpdate, db: Session = Depends(get_db)) -> SignalRead:
    """
    Обновить существующий сигнал.
    """
    signal = signal_service.update_signal(db, signal_id, signal_in)
    if not signal:
        logger.warning(f"Signal {signal_id} not found for update.")
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal

@router.delete("/{signal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_signal(signal_id: int, db: Session = Depends(get_db)) -> None:
    """
    Удалить сигнал по ID.
    """
    success = signal_service.delete_signal(db, signal_id)
    if not success:
        logger.warning(f"Signal {signal_id} not found for delete.")
        raise HTTPException(status_code=404, detail="Signal not found") 