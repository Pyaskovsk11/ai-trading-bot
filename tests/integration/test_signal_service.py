import pytest
from app.services import signal_service
from app.schemas.signal import SignalCreate
from sqlalchemy.orm import Session

def test_create_and_get_signal(test_db: Session):
    signal_data = {
        "symbol": "BTCUSDT",
        "direction": "BUY",
        "confidence": 0.8,
        "source": "unit_test",
        "asset_pair": "BTC/USDT",
        "signal_type": "BUY",
        "confidence_score": 0.9,
        "price_at_signal": 50000.0,
        "time_frame": "1h",
        "status": "NEW"
    }
    signal = signal_service.create_signal(test_db, SignalCreate(**signal_data))
    assert signal.symbol == signal_data["symbol"]
    fetched = signal_service.get_signal_by_id(test_db, signal.id)
    assert fetched is not None
    assert fetched.signal_type == signal_data["signal_type"] 