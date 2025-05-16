import logging

logger = logging.getLogger(__name__)

def calculate_position_size(balance: float, risk_per_trade: float, stop_loss_pct: float) -> float:
    """
    Рассчитывает размер позиции исходя из баланса, риска на сделку и процента стоп-лосса.
    """
    try:
        if stop_loss_pct <= 0:
            logger.error("Stop loss percent must be positive")
            return 0.0
        size = balance * risk_per_trade / stop_loss_pct
        logger.info(f"Position size calculated: {size} (balance={balance}, risk={risk_per_trade}, stop_loss_pct={stop_loss_pct})")
        return size
    except Exception as e:
        logger.error(f"Error calculating position size: {e}")
        return 0.0

def calculate_stop_loss(entry_price: float, stop_loss_pct: float, direction: str = "LONG") -> float:
    """
    Рассчитывает цену стоп-лосса для long/short позиции.
    """
    try:
        if direction == "LONG":
            stop_loss = entry_price * (1 - stop_loss_pct)
        else:
            stop_loss = entry_price * (1 + stop_loss_pct)
        logger.info(f"Stop loss calculated: {stop_loss} (entry={entry_price}, pct={stop_loss_pct}, dir={direction})")
        return stop_loss
    except Exception as e:
        logger.error(f"Error calculating stop loss: {e}")
        return entry_price 