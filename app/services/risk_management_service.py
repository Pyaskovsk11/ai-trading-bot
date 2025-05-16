import logging
from sqlalchemy.orm import Session
from app.utils.risk_management import calculate_position_size, calculate_stop_loss

logger = logging.getLogger(__name__)

def apply_risk_management(balance: float, entry_price: float, risk_per_trade: float, stop_loss_pct: float, direction: str = "LONG") -> dict:
    """
    Применяет риск-менеджмент: рассчитывает размер позиции и стоп-лосс.
    """
    try:
        position_size = calculate_position_size(balance, risk_per_trade, stop_loss_pct)
        stop_loss = calculate_stop_loss(entry_price, stop_loss_pct, direction)
        logger.info(f"Risk management applied: size={position_size}, stop_loss={stop_loss}")
        return {"position_size": position_size, "stop_loss": stop_loss}
    except Exception as e:
        logger.error(f"Error in risk management: {e}")
        return {"position_size": 0.0, "stop_loss": entry_price} 