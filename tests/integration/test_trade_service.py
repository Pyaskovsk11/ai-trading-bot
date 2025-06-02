import pytest
from app.services import trade_service, user_service, signal_service
from app.schemas.trade import TradeCreate
from app.schemas.user import UserCreate
from app.schemas.signal import SignalCreate
from sqlalchemy.orm import Session

def test_create_and_get_trade(test_db: Session):
    user = user_service.create_user(test_db, UserCreate(telegram_id="12345", username="trader"))
    signal = signal_service.create_signal(test_db, SignalCreate(symbol="BTCUSDT", direction="BUY", confidence=0.8, source="unit_test", asset_pair="BTC/USDT", signal_type="BUY", confidence_score=0.9, price_at_signal=50000.0, time_frame="1h", status="NEW"))
    trade_data = {"symbol": "BTCUSDT", "side": "BUY", "quantity": 1.0, "status": "OPEN", "entry_price": 50000.0, "volume": 1.0, "signal_id": signal.id, "user_id": user.id}
    trade = trade_service.create_trade(test_db, TradeCreate(**trade_data))
    assert trade.symbol == trade_data["symbol"]
    fetched = trade_service.get_trade_by_id(test_db, trade.id)
    assert fetched is not None
    assert fetched.user_id == user.id 