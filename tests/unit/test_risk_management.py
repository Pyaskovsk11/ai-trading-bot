from app.utils import risk_management

def test_calculate_position_size():
    balance = 1000
    risk_per_trade = 0.01
    stop_loss_pct = 0.02
    size = risk_management.calculate_position_size(balance, risk_per_trade, stop_loss_pct)
    assert isinstance(size, float)
    assert size > 0

def test_calculate_stop_loss():
    entry_price = 100
    stop_loss_pct = 0.02
    stop_loss = risk_management.calculate_stop_loss(entry_price, stop_loss_pct)
    assert isinstance(stop_loss, float)
    assert stop_loss < entry_price 