import pytest
from datetime import datetime

def test_full_trading_flow(client):
    # 1. Создать сигнал через API
    signal_data = {
        "asset_pair": "BTC/USDT",
        "signal_type": "BUY",
        "confidence_score": 0.9,
        "price_at_signal": 50000.0,
        "target_price": 52000.0,
        "stop_loss": 49500.0,
        "time_frame": "1h",
        "technical_indicators": {"RSI": 70, "MACD": 1.2}
    }
    create_resp = client.post("/api/v1/signals/", json=signal_data)
    assert create_resp.status_code == 200
    signal = create_resp.json()
    assert signal["asset_pair"] == signal_data["asset_pair"]
    signal_id = signal["id"]

    # 2. Получить сигнал по id
    get_resp = client.get(f"/api/v1/signals/{signal_id}")
    assert get_resp.status_code == 200
    signal_fetched = get_resp.json()
    assert signal_fetched["id"] == signal_id

    # 3. Получить детали сигнала (XAI объяснение)
    details_resp = client.get(f"/api/v1/signals/{signal_id}/details")
    assert details_resp.status_code == 200
    details = details_resp.json()
    assert "xai_explanation" in details
    assert details["xai_explanation"] is not None 