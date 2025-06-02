from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.signal import SignalCreate, SignalResponse
from app.services.signal_service import SignalService

router = APIRouter()

@router.post("/signals/", response_model=SignalResponse)
def create_signal(
    signal: SignalCreate,
    db: Session = Depends(get_db)
) -> SignalResponse:
    """
    Создает новый торговый сигнал.
    """
    signal_service = SignalService(db)
    return signal_service.create_signal(signal)

@router.get("/signals/", response_model=List[SignalResponse])
def get_signals(
    skip: int = 0,
    limit: int = 100,
    symbol: str = None,
    db: Session = Depends(get_db)
) -> List[SignalResponse]:
    """
    Получает список торговых сигналов.
    """
    signal_service = SignalService(db)
    return signal_service.get_signals(skip=skip, limit=limit, symbol=symbol)

@router.get("/signals/{signal_id}", response_model=SignalResponse)
def get_signal(
    signal_id: int,
    db: Session = Depends(get_db)
) -> SignalResponse:
    """
    Получает информацию о конкретном торговом сигнале.
    """
    signal_service = SignalService(db)
    signal = signal_service.get_signal(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal

@router.post("/signals/{signal_id}/execute")
def execute_signal(
    signal_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """
    Выполняет торговый сигнал.
    """
    signal_service = SignalService(db)
    success = signal_service.execute_signal(signal_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to execute signal")
    return {"status": "success", "message": "Signal executed successfully"} 