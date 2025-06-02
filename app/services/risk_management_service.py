import logging
from sqlalchemy.orm import Session
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class RiskManagementService:
    """Сервис управления рисками"""
    
    def __init__(self):
        self.max_risk_per_trade = 0.05  # 5% максимальный риск на сделку
        self.max_daily_loss = 0.10      # 10% максимальная дневная просадка
        logger.info("Risk Management Service инициализирован")
    
    def calculate_position_size(self, balance: float, risk_per_trade: float, stop_loss_pct: float) -> float:
        """Расчет размера позиции на основе риска"""
        try:
            # Ограничиваем риск максимальным значением
            risk = min(risk_per_trade, self.max_risk_per_trade)
            
            # Размер позиции = (Баланс * Риск) / Стоп-лосс%
            position_size = (balance * risk) / stop_loss_pct
            
            logger.info(f"Calculated position size: {position_size} (risk: {risk}, stop_loss: {stop_loss_pct})")
            return position_size
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def calculate_stop_loss(self, entry_price: float, stop_loss_pct: float, direction: str = "LONG") -> float:
        """Расчет уровня стоп-лосса"""
        try:
            if direction.upper() == "LONG":
                stop_loss = entry_price * (1 - stop_loss_pct)
            else:  # SHORT
                stop_loss = entry_price * (1 + stop_loss_pct)
            
            logger.info(f"Calculated stop loss: {stop_loss} for {direction} position")
            return stop_loss
        except Exception as e:
            logger.error(f"Error calculating stop loss: {e}")
            return entry_price

def apply_risk_management(balance: float, entry_price: float, risk_per_trade: float, stop_loss_pct: float, direction: str = "LONG") -> dict:
    """
    Применяет риск-менеджмент: рассчитывает размер позиции и стоп-лосс.
    """
    service = RiskManagementService()
    try:
        position_size = service.calculate_position_size(balance, risk_per_trade, stop_loss_pct)
        stop_loss = service.calculate_stop_loss(entry_price, stop_loss_pct, direction)
        logger.info(f"Risk management applied: size={position_size}, stop_loss={stop_loss}")
        return {"position_size": position_size, "stop_loss": stop_loss}
    except Exception as e:
        logger.error(f"Error in risk management: {e}")
        return {"position_size": 0.0, "stop_loss": entry_price} 