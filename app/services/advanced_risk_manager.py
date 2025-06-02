"""
Advanced Risk Management System
Продвинутая система управления рисками с VaR, корреляционным анализом и защитой от просадок
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    """Рыночные режимы"""
    BULL = "bull"           # Бычий рынок
    BEAR = "bear"           # Медвежий рынок
    SIDEWAYS = "sideways"   # Боковой тренд
    VOLATILE = "volatile"   # Высокая волатильность
    UNKNOWN = "unknown"     # Неопределенный

@dataclass
class RiskMetrics:
    """Метрики риска"""
    var_95: float           # Value at Risk 95%
    var_99: float           # Value at Risk 99%
    expected_shortfall: float  # Expected Shortfall
    max_drawdown: float     # Максимальная просадка
    sharpe_ratio: float     # Коэффициент Шарпа
    sortino_ratio: float    # Коэффициент Сортино
    calmar_ratio: float     # Коэффициент Калмара
    volatility: float       # Волатильность
    beta: float             # Бета к рынку

@dataclass
class PositionRisk:
    """Риск позиции"""
    symbol: str
    position_size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    risk_contribution: float  # Вклад в общий риск портфеля
    correlation_risk: float   # Корреляционный риск
    var_contribution: float   # Вклад в VaR портфеля

@dataclass
class RiskLimits:
    """Лимиты риска"""
    max_portfolio_var: float = 0.02      # 2% максимальный VaR портфеля
    max_position_size: float = 0.10      # 10% максимальный размер позиции
    max_correlation: float = 0.70        # 70% максимальная корреляция
    max_drawdown: float = 0.15           # 15% максимальная просадка
    max_sector_exposure: float = 0.30    # 30% максимальная экспозиция по сектору
    min_diversification: int = 5         # Минимум 5 позиций

class AdvancedRiskManager:
    """
    Продвинутая система управления рисками
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.peak_capital = initial_capital
        
        # Лимиты риска
        self.risk_limits = RiskLimits()
        
        # История портфеля
        self.portfolio_history: List[Dict] = []
        self.returns_history: List[float] = []
        
        # Текущие позиции
        self.positions: Dict[str, PositionRisk] = {}
        
        # Корреляционная матрица
        self.correlation_matrix: Optional[pd.DataFrame] = None
        self.last_correlation_update = None
        
        # Защита от просадок
        self.drawdown_protection_active = False
        self.current_drawdown = 0.0
        
        # Рыночный режим
        self.current_market_regime = MarketRegime.UNKNOWN
        
        logger.info("AdvancedRiskManager инициализирован")
    
    async def calculate_var(self, returns: List[float], confidence: float = 0.95) -> float:
        """
        Расчет Value at Risk (VaR)
        """
        try:
            if len(returns) < 30:
                logger.warning("Недостаточно данных для расчета VaR")
                return 0.0
            
            returns_array = np.array(returns)
            
            # Параметрический VaR (предполагаем нормальное распределение)
            mean_return = np.mean(returns_array)
            std_return = np.std(returns_array)
            
            # Z-score для заданного уровня доверия
            z_score = {
                0.90: 1.282,
                0.95: 1.645,
                0.99: 2.326
            }.get(confidence, 1.645)
            
            parametric_var = -(mean_return - z_score * std_return)
            
            # Исторический VaR
            percentile = (1 - confidence) * 100
            historical_var = -np.percentile(returns_array, percentile)
            
            # Используем максимум из двух методов (консервативный подход)
            var = max(parametric_var, historical_var)
            
            return max(var, 0.0)  # VaR не может быть отрицательным
            
        except Exception as e:
            logger.error(f"Ошибка расчета VaR: {e}")
            return 0.0
    
    async def calculate_expected_shortfall(self, returns: List[float], confidence: float = 0.95) -> float:
        """
        Расчет Expected Shortfall (Conditional VaR)
        """
        try:
            if len(returns) < 30:
                return 0.0
            
            returns_array = np.array(returns)
            percentile = (1 - confidence) * 100
            var_threshold = np.percentile(returns_array, percentile)
            
            # Expected Shortfall = среднее значение потерь, превышающих VaR
            tail_losses = returns_array[returns_array <= var_threshold]
            
            if len(tail_losses) > 0:
                expected_shortfall = -np.mean(tail_losses)
            else:
                expected_shortfall = 0.0
            
            return max(expected_shortfall, 0.0)
            
        except Exception as e:
            logger.error(f"Ошибка расчета Expected Shortfall: {e}")
            return 0.0
    
    async def calculate_portfolio_metrics(self) -> RiskMetrics:
        """
        Расчет метрик риска портфеля
        """
        try:
            if len(self.returns_history) < 30:
                logger.warning("Недостаточно данных для расчета метрик")
                return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0)
            
            returns = np.array(self.returns_history)
            
            # VaR расчеты
            var_95 = await self.calculate_var(self.returns_history, 0.95)
            var_99 = await self.calculate_var(self.returns_history, 0.99)
            
            # Expected Shortfall
            expected_shortfall = await self.calculate_expected_shortfall(self.returns_history, 0.95)
            
            # Максимальная просадка
            max_drawdown = self.calculate_max_drawdown()
            
            # Волатильность (годовая)
            volatility = np.std(returns) * np.sqrt(252)  # 252 торговых дня
            
            # Коэффициент Шарпа (предполагаем безрисковую ставку 2%)
            risk_free_rate = 0.02
            mean_return = np.mean(returns) * 252  # Годовая доходность
            sharpe_ratio = (mean_return - risk_free_rate) / volatility if volatility > 0 else 0
            
            # Коэффициент Сортино (только отрицательная волатильность)
            negative_returns = returns[returns < 0]
            downside_volatility = np.std(negative_returns) * np.sqrt(252) if len(negative_returns) > 0 else 0
            sortino_ratio = (mean_return - risk_free_rate) / downside_volatility if downside_volatility > 0 else 0
            
            # Коэффициент Калмара
            calmar_ratio = mean_return / max_drawdown if max_drawdown > 0 else 0
            
            # Бета (пока заглушка, нужны данные рынка)
            beta = 1.0
            
            return RiskMetrics(
                var_95=var_95,
                var_99=var_99,
                expected_shortfall=expected_shortfall,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                volatility=volatility,
                beta=beta
            )
            
        except Exception as e:
            logger.error(f"Ошибка расчета метрик портфеля: {e}")
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0)
    
    def calculate_max_drawdown(self) -> float:
        """
        Расчет максимальной просадки
        """
        try:
            if len(self.portfolio_history) < 2:
                return 0.0
            
            equity_curve = [entry['total_value'] for entry in self.portfolio_history]
            peak = equity_curve[0]
            max_dd = 0.0
            
            for value in equity_curve:
                if value > peak:
                    peak = value
                
                drawdown = (peak - value) / peak
                max_dd = max(max_dd, drawdown)
            
            return max_dd
            
        except Exception as e:
            logger.error(f"Ошибка расчета максимальной просадки: {e}")
            return 0.0
    
    async def update_correlation_matrix(self, price_data: Dict[str, List[float]]):
        """
        Обновление корреляционной матрицы активов
        """
        try:
            if len(price_data) < 2:
                return
            
            # Создаем DataFrame с ценами
            df = pd.DataFrame(price_data)
            
            # Рассчитываем доходности
            returns_df = df.pct_change().dropna()
            
            # Рассчитываем корреляционную матрицу
            self.correlation_matrix = returns_df.corr()
            self.last_correlation_update = datetime.now()
            
            logger.info(f"Корреляционная матрица обновлена для {len(price_data)} активов")
            
        except Exception as e:
            logger.error(f"Ошибка обновления корреляционной матрицы: {e}")
    
    def get_correlation_risk(self, symbol1: str, symbol2: str) -> float:
        """
        Получение корреляционного риска между двумя активами
        """
        try:
            if self.correlation_matrix is None:
                return 0.0
            
            if symbol1 in self.correlation_matrix.index and symbol2 in self.correlation_matrix.columns:
                correlation = self.correlation_matrix.loc[symbol1, symbol2]
                return abs(correlation)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Ошибка получения корреляции между {symbol1} и {symbol2}: {e}")
            return 0.0
    
    async def adaptive_position_sizing(self, 
                                     symbol: str,
                                     signal_confidence: float,
                                     volatility: float,
                                     market_regime: MarketRegime = None) -> float:
        """
        Адаптивный расчет размера позиции
        """
        try:
            # Базовый размер позиции (% от капитала)
            base_position_size = 0.02  # 2%
            
            # Корректировка на уверенность сигнала
            confidence_multiplier = signal_confidence
            
            # Корректировка на волатильность (обратная зависимость)
            volatility_multiplier = 1 / (1 + volatility * 2)
            
            # Корректировка на рыночный режим
            regime_multiplier = self._get_regime_multiplier(market_regime or self.current_market_regime)
            
            # Корректировка на текущую просадку
            drawdown_multiplier = self._get_drawdown_multiplier()
            
            # Корректировка на корреляционный риск
            correlation_multiplier = self._get_correlation_multiplier(symbol)
            
            # Финальный размер позиции
            adjusted_size = (base_position_size * 
                           confidence_multiplier * 
                           volatility_multiplier * 
                           regime_multiplier * 
                           drawdown_multiplier * 
                           correlation_multiplier)
            
            # Применяем лимиты
            max_position = self.risk_limits.max_position_size
            adjusted_size = min(adjusted_size, max_position)
            
            logger.info(f"Адаптивный размер позиции для {symbol}: {adjusted_size:.4f} "
                       f"(уверенность: {confidence_multiplier:.2f}, "
                       f"волатильность: {volatility_multiplier:.2f}, "
                       f"режим: {regime_multiplier:.2f})")
            
            return adjusted_size
            
        except Exception as e:
            logger.error(f"Ошибка расчета адаптивного размера позиции: {e}")
            return 0.01  # Минимальный размер
    
    def _get_regime_multiplier(self, regime: MarketRegime) -> float:
        """Получение мультипликатора для рыночного режима"""
        multipliers = {
            MarketRegime.BULL: 1.2,      # Увеличиваем позиции в бычьем рынке
            MarketRegime.BEAR: 0.6,      # Уменьшаем в медвежьем
            MarketRegime.SIDEWAYS: 0.8,  # Умеренно в боковом тренде
            MarketRegime.VOLATILE: 0.5,  # Сильно уменьшаем при высокой волатильности
            MarketRegime.UNKNOWN: 0.7    # Консервативно при неопределенности
        }
        return multipliers.get(regime, 0.7)
    
    def _get_drawdown_multiplier(self) -> float:
        """Получение мультипликатора на основе текущей просадки"""
        if self.current_drawdown < 0.05:  # < 5%
            return 1.0
        elif self.current_drawdown < 0.10:  # 5-10%
            return 0.8
        elif self.current_drawdown < 0.15:  # 10-15%
            return 0.5
        else:  # > 15%
            return 0.2  # Сильно уменьшаем размеры позиций
    
    def _get_correlation_multiplier(self, symbol: str) -> float:
        """Получение мультипликатора на основе корреляционного риска"""
        try:
            if not self.positions or self.correlation_matrix is None:
                return 1.0
            
            max_correlation = 0.0
            
            for existing_symbol in self.positions.keys():
                if existing_symbol != symbol:
                    correlation = self.get_correlation_risk(symbol, existing_symbol)
                    max_correlation = max(max_correlation, correlation)
            
            # Если корреляция высокая, уменьшаем размер позиции
            if max_correlation > self.risk_limits.max_correlation:
                return 0.5  # Уменьшаем на 50%
            elif max_correlation > 0.5:
                return 0.8  # Уменьшаем на 20%
            else:
                return 1.0  # Без изменений
                
        except Exception as e:
            logger.error(f"Ошибка расчета корреляционного мультипликатора: {e}")
            return 1.0
    
    async def dynamic_stop_loss(self, 
                              entry_price: float,
                              atr: float,
                              volatility: float,
                              trend_strength: float,
                              position_type: str = "LONG") -> float:
        """
        Динамический расчет стоп-лосса
        """
        try:
            # Базовый стоп на основе ATR
            base_stop_distance = atr * 2.0
            
            # Корректировка на волатильность
            volatility_adjustment = volatility * 0.5
            
            # Корректировка на силу тренда (слабый тренд = более широкий стоп)
            trend_adjustment = (1 - trend_strength) * 0.3
            
            # Корректировка на рыночный режим
            regime_adjustment = self._get_stop_loss_regime_adjustment()
            
            # Финальное расстояние стоп-лосса
            final_stop_distance = base_stop_distance * (
                1 + volatility_adjustment + trend_adjustment + regime_adjustment
            )
            
            # Рассчитываем цену стоп-лосса
            if position_type.upper() == "LONG":
                stop_loss_price = entry_price - final_stop_distance
            else:  # SHORT
                stop_loss_price = entry_price + final_stop_distance
            
            logger.info(f"Динамический стоп-лосс: {stop_loss_price:.2f} "
                       f"(расстояние: {final_stop_distance:.2f}, "
                       f"ATR: {atr:.2f})")
            
            return stop_loss_price
            
        except Exception as e:
            logger.error(f"Ошибка расчета динамического стоп-лосса: {e}")
            return entry_price * 0.95 if position_type.upper() == "LONG" else entry_price * 1.05
    
    def _get_stop_loss_regime_adjustment(self) -> float:
        """Корректировка стоп-лосса на основе рыночного режима"""
        adjustments = {
            MarketRegime.BULL: -0.1,     # Более узкие стопы в бычьем рынке
            MarketRegime.BEAR: 0.2,      # Более широкие в медвежьем
            MarketRegime.SIDEWAYS: 0.0,  # Без изменений в боковом
            MarketRegime.VOLATILE: 0.3,  # Широкие стопы при волатильности
            MarketRegime.UNKNOWN: 0.1    # Слегка консервативно
        }
        return adjustments.get(self.current_market_regime, 0.1)
    
    async def check_risk_limits(self) -> Dict[str, bool]:
        """
        Проверка соблюдения лимитов риска
        """
        try:
            violations = {}
            
            # Проверка VaR портфеля
            metrics = await self.calculate_portfolio_metrics()
            violations['var_limit'] = metrics.var_95 > self.risk_limits.max_portfolio_var
            
            # Проверка максимальной просадки
            violations['drawdown_limit'] = self.current_drawdown > self.risk_limits.max_drawdown
            
            # Проверка размеров позиций
            violations['position_size_limit'] = any(
                pos.position_size > self.risk_limits.max_position_size 
                for pos in self.positions.values()
            )
            
            # Проверка корреляций
            violations['correlation_limit'] = self._check_correlation_limits()
            
            # Проверка диверсификации
            violations['diversification_limit'] = len(self.positions) < self.risk_limits.min_diversification
            
            return violations
            
        except Exception as e:
            logger.error(f"Ошибка проверки лимитов риска: {e}")
            return {}
    
    def _check_correlation_limits(self) -> bool:
        """Проверка лимитов корреляции"""
        try:
            if len(self.positions) < 2 or self.correlation_matrix is None:
                return False
            
            symbols = list(self.positions.keys())
            
            for i, symbol1 in enumerate(symbols):
                for symbol2 in symbols[i+1:]:
                    correlation = self.get_correlation_risk(symbol1, symbol2)
                    if correlation > self.risk_limits.max_correlation:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка проверки корреляционных лимитов: {e}")
            return False
    
    async def activate_drawdown_protection(self):
        """
        Активация защиты от просадок
        """
        try:
            self.drawdown_protection_active = True
            
            logger.warning(f"🛡️ АКТИВИРОВАНА ЗАЩИТА ОТ ПРОСАДОК! "
                          f"Текущая просадка: {self.current_drawdown:.2%}")
            
            # Уменьшаем размеры всех позиций на 50%
            for symbol, position in self.positions.items():
                position.position_size *= 0.5
                logger.info(f"Размер позиции {symbol} уменьшен до {position.position_size:.4f}")
            
            # Повышаем пороги уверенности для новых сигналов
            # Это будет обрабатываться в TradingStrategyManager
            
        except Exception as e:
            logger.error(f"Ошибка активации защиты от просадок: {e}")
    
    async def deactivate_drawdown_protection(self):
        """
        Деактивация защиты от просадок
        """
        try:
            self.drawdown_protection_active = False
            logger.info("✅ Защита от просадок деактивирована")
            
        except Exception as e:
            logger.error(f"Ошибка деактивации защиты от просадок: {e}")
    
    def update_portfolio_value(self, total_value: float):
        """
        Обновление стоимости портфеля
        """
        try:
            # Обновляем текущий капитал
            previous_value = self.current_capital
            self.current_capital = total_value
            
            # Рассчитываем доходность
            if previous_value > 0:
                return_pct = (total_value - previous_value) / previous_value
                self.returns_history.append(return_pct)
                
                # Ограничиваем историю последними 1000 записями
                if len(self.returns_history) > 1000:
                    self.returns_history = self.returns_history[-1000:]
            
            # Обновляем пиковое значение
            if total_value > self.peak_capital:
                self.peak_capital = total_value
                
                # Деактивируем защиту от просадок при новом максимуме
                if self.drawdown_protection_active:
                    asyncio.create_task(self.deactivate_drawdown_protection())
            
            # Рассчитываем текущую просадку
            self.current_drawdown = (self.peak_capital - total_value) / self.peak_capital
            
            # Проверяем необходимость активации защиты от просадок
            if (self.current_drawdown > self.risk_limits.max_drawdown and 
                not self.drawdown_protection_active):
                asyncio.create_task(self.activate_drawdown_protection())
            
            # Добавляем в историю портфеля
            self.portfolio_history.append({
                'timestamp': datetime.now(),
                'total_value': total_value,
                'drawdown': self.current_drawdown,
                'peak_value': self.peak_capital
            })
            
            # Ограничиваем историю
            if len(self.portfolio_history) > 1000:
                self.portfolio_history = self.portfolio_history[-1000:]
            
        except Exception as e:
            logger.error(f"Ошибка обновления стоимости портфеля: {e}")
    
    def get_risk_summary(self) -> Dict:
        """
        Получение сводки по рискам
        """
        try:
            return {
                'current_capital': self.current_capital,
                'peak_capital': self.peak_capital,
                'current_drawdown': self.current_drawdown,
                'drawdown_protection_active': self.drawdown_protection_active,
                'total_positions': len(self.positions),
                'market_regime': self.current_market_regime.value,
                'risk_limits': {
                    'max_portfolio_var': self.risk_limits.max_portfolio_var,
                    'max_position_size': self.risk_limits.max_position_size,
                    'max_correlation': self.risk_limits.max_correlation,
                    'max_drawdown': self.risk_limits.max_drawdown
                }
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения сводки рисков: {e}")
            return {}

# Глобальный экземпляр продвинутого риск-менеджера
advanced_risk_manager = AdvancedRiskManager() 