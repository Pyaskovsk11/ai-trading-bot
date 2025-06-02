"""
Profitable Strategy Engine - Движок стратегии с фокусом на прибыльность
Цель: Превратить -0.070% в +1-3% доходность при сохранении хорошего винрейта
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ProfitOptimizationMode(Enum):
    """Режимы оптимизации прибыли"""
    CONSERVATIVE = "conservative"    # Консервативный - низкий риск
    BALANCED = "balanced"           # Сбалансированный - средний риск  
    AGGRESSIVE = "aggressive"       # Агрессивный - высокий риск

@dataclass
class ProfitableSignal:
    """Сигнал оптимизированный для прибыльности"""
    signal: str                    # buy/sell/hold
    confidence: float              # 0.0-1.0
    entry_price: float
    stop_loss: float
    take_profit_1: float           # Первый тейк-профит (50% позиции)
    take_profit_2: float           # Второй тейк-профит (30% позиции)  
    take_profit_3: float           # Третий тейк-профит (20% позиции)
    trailing_stop: bool            # Использовать трейлинг стоп
    max_hold_time: int             # Максимальное время удержания (часы)
    risk_reward_ratio: float       # Соотношение риск/прибыль
    strategy_type: str
    reason: str
    metadata: Dict

class ProfitableStrategyEngine:
    """
    Движок стратегии оптимизированный для максимальной прибыльности
    """
    
    def __init__(self, optimization_mode: ProfitOptimizationMode = ProfitOptimizationMode.BALANCED):
        self.optimization_mode = optimization_mode
        self.min_risk_reward_ratio = self._get_min_risk_reward_ratio()
        self.profit_targets = self._get_profit_targets()
        self.stop_loss_levels = self._get_stop_loss_levels()
        
        logger.info(f"ProfitableStrategyEngine инициализирован в режиме {optimization_mode.value}")
    
    def _get_min_risk_reward_ratio(self) -> float:
        """Минимальное соотношение риск/прибыль для разных режимов"""
        ratios = {
            ProfitOptimizationMode.CONSERVATIVE: 1.5,  # 1:1.5 минимум
            ProfitOptimizationMode.BALANCED: 2.0,      # 1:2 минимум
            ProfitOptimizationMode.AGGRESSIVE: 2.5     # 1:2.5 минимум
        }
        return ratios[self.optimization_mode]
    
    def _get_profit_targets(self) -> List[float]:
        """Уровни тейк-профитов для разных режимов"""
        targets = {
            ProfitOptimizationMode.CONSERVATIVE: [0.015, 0.025, 0.035],  # 1.5%, 2.5%, 3.5%
            ProfitOptimizationMode.BALANCED: [0.020, 0.035, 0.050],      # 2%, 3.5%, 5%
            ProfitOptimizationMode.AGGRESSIVE: [0.025, 0.045, 0.070]     # 2.5%, 4.5%, 7%
        }
        return targets[self.optimization_mode]
    
    def _get_stop_loss_levels(self) -> float:
        """Уровни стоп-лоссов для разных режимов"""
        levels = {
            ProfitOptimizationMode.CONSERVATIVE: 0.010,  # 1% стоп-лосс
            ProfitOptimizationMode.BALANCED: 0.015,      # 1.5% стоп-лосс
            ProfitOptimizationMode.AGGRESSIVE: 0.020     # 2% стоп-лосс
        }
        return levels[self.optimization_mode]
    
    async def analyze_profitable_signal(self, 
                                      indicators: Dict, 
                                      market_regime: str, 
                                      price: float, 
                                      timestamp: datetime,
                                      volume_profile: Dict = None) -> Optional[ProfitableSignal]:
        """
        Анализ сигнала с фокусом на прибыльность
        """
        try:
            # Базовый анализ качества сигнала
            signal_quality = self._assess_signal_quality(indicators, market_regime, volume_profile)
            
            if signal_quality['score'] < 70:  # Высокий порог качества
                return None
            
            # Определяем направление сигнала
            signal_direction = self._determine_signal_direction(indicators, market_regime)
            
            if signal_direction == 'hold':
                return None
            
            # Рассчитываем оптимальные уровни входа и выхода
            levels = self._calculate_optimal_levels(price, signal_direction, signal_quality)
            
            # Проверяем соотношение риск/прибыль
            if levels['risk_reward_ratio'] < self.min_risk_reward_ratio:
                logger.debug(f"Сигнал отклонен: низкое соотношение риск/прибыль {levels['risk_reward_ratio']:.2f}")
                return None
            
            # Определяем время удержания позиции
            max_hold_time = self._calculate_max_hold_time(signal_quality, market_regime)
            
            # Создаем прибыльный сигнал
            profitable_signal = ProfitableSignal(
                signal=signal_direction,
                confidence=signal_quality['confidence'],
                entry_price=price,
                stop_loss=levels['stop_loss'],
                take_profit_1=levels['take_profit_1'],
                take_profit_2=levels['take_profit_2'],
                take_profit_3=levels['take_profit_3'],
                trailing_stop=levels['use_trailing_stop'],
                max_hold_time=max_hold_time,
                risk_reward_ratio=levels['risk_reward_ratio'],
                strategy_type=f"profitable_{self.optimization_mode.value}",
                reason=signal_quality['reason'],
                metadata={
                    'signal_quality': signal_quality,
                    'market_regime': market_regime,
                    'optimization_mode': self.optimization_mode.value,
                    'profit_targets': self.profit_targets,
                    'indicators_used': list(indicators.keys())
                }
            )
            
            logger.info(f"Прибыльный сигнал: {signal_direction} @ ${price:.2f}, "
                       f"R/R: {levels['risk_reward_ratio']:.2f}, "
                       f"качество: {signal_quality['score']}")
            
            return profitable_signal
            
        except Exception as e:
            logger.error(f"Ошибка анализа прибыльного сигнала: {e}")
            return None
    
    def _assess_signal_quality(self, indicators: Dict, market_regime: str, volume_profile: Dict = None) -> Dict:
        """Оценка качества сигнала для прибыльности"""
        
        quality_score = 0
        confidence_factors = []
        
        # 1. RSI анализ (вес: 20 баллов)
        rsi = indicators.get('rsi', 50)
        if 25 <= rsi <= 35:  # Сильная перепроданность
            quality_score += 20
            confidence_factors.append(f"RSI перепроданность ({rsi:.1f})")
        elif 65 <= rsi <= 75:  # Сильная перекупленность
            quality_score += 20
            confidence_factors.append(f"RSI перекупленность ({rsi:.1f})")
        elif 35 <= rsi <= 45 or 55 <= rsi <= 65:  # Умеренные уровни
            quality_score += 10
            confidence_factors.append(f"RSI умеренный ({rsi:.1f})")
        
        # 2. MACD сигналы (вес: 25 баллов)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_histogram = indicators.get('macd_histogram', 0)
        
        # Сильные MACD сигналы
        if macd > macd_signal and macd_histogram > 0 and macd_histogram > indicators.get('prev_macd_histogram', 0):
            quality_score += 25
            confidence_factors.append("MACD сильный бычий сигнал с ускорением")
        elif macd < macd_signal and macd_histogram < 0 and macd_histogram < indicators.get('prev_macd_histogram', 0):
            quality_score += 25
            confidence_factors.append("MACD сильный медвежий сигнал с ускорением")
        elif macd > macd_signal and macd_histogram > 0:
            quality_score += 15
            confidence_factors.append("MACD бычий сигнал")
        elif macd < macd_signal and macd_histogram < 0:
            quality_score += 15
            confidence_factors.append("MACD медвежий сигнал")
        
        # 3. Bollinger Bands позиция (вес: 15 баллов)
        bb_position = indicators.get('bb_position', 0.5)
        if bb_position < 0.1:  # Очень близко к нижней границе
            quality_score += 15
            confidence_factors.append("Цена у нижней границы BB")
        elif bb_position > 0.9:  # Очень близко к верхней границе
            quality_score += 15
            confidence_factors.append("Цена у верхней границы BB")
        elif bb_position < 0.2 or bb_position > 0.8:
            quality_score += 10
            confidence_factors.append("Цена в экстремальной зоне BB")
        
        # 4. Трендовый анализ (вес: 20 баллов)
        sma_20 = indicators.get('sma_20', 0)
        sma_50 = indicators.get('sma_50', 0)
        ema_12 = indicators.get('ema_12', 0)
        ema_26 = indicators.get('ema_26', 0)
        current_price = indicators.get('current_price', 0)
        
        # Сильные трендовые сигналы
        if current_price > ema_12 > ema_26 > sma_20 > sma_50:
            quality_score += 20
            confidence_factors.append("Сильный восходящий тренд")
        elif current_price < ema_12 < ema_26 < sma_20 < sma_50:
            quality_score += 20
            confidence_factors.append("Сильный нисходящий тренд")
        elif current_price > ema_12 > ema_26:
            quality_score += 12
            confidence_factors.append("Краткосрочный восходящий тренд")
        elif current_price < ema_12 < ema_26:
            quality_score += 12
            confidence_factors.append("Краткосрочный нисходящий тренд")
        
        # 5. Объемный анализ (вес: 10 баллов)
        volume_ratio = indicators.get('volume_ratio', 1.0)
        if volume_ratio > 2.0:  # Очень высокий объем
            quality_score += 10
            confidence_factors.append(f"Очень высокий объем ({volume_ratio:.1f}x)")
        elif volume_ratio > 1.5:  # Высокий объем
            quality_score += 7
            confidence_factors.append(f"Высокий объем ({volume_ratio:.1f}x)")
        elif volume_ratio < 0.5:  # Низкий объем - штраф
            quality_score -= 5
            confidence_factors.append(f"Низкий объем ({volume_ratio:.1f}x)")
        
        # 6. Волатильность (вес: 10 баллов)
        volatility = indicators.get('volatility', 0.02)
        if 0.015 <= volatility <= 0.04:  # Оптимальная волатильность для торговли
            quality_score += 10
            confidence_factors.append(f"Оптимальная волатильность ({volatility:.3f})")
        elif volatility > 0.08:  # Слишком высокая волатильность - штраф
            quality_score -= 10
            confidence_factors.append(f"Высокая волатильность ({volatility:.3f})")
        
        # Бонусы за рыночный режим
        if market_regime in ['bull_trend', 'bear_trend']:
            quality_score += 5
            confidence_factors.append(f"Трендовый рынок ({market_regime})")
        
        # Нормализуем оценку
        quality_score = max(0, min(100, quality_score))
        confidence = quality_score / 100.0
        
        return {
            'score': quality_score,
            'confidence': confidence,
            'reason': "; ".join(confidence_factors[:4]),  # Топ-4 фактора
            'all_factors': confidence_factors
        }
    
    def _determine_signal_direction(self, indicators: Dict, market_regime: str) -> str:
        """Определение направления сигнала"""
        
        buy_signals = 0
        sell_signals = 0
        
        # RSI сигналы
        rsi = indicators.get('rsi', 50)
        if rsi < 35:
            buy_signals += 2
        elif rsi > 65:
            sell_signals += 2
        
        # MACD сигналы
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        if macd > macd_signal:
            buy_signals += 2
        else:
            sell_signals += 2
        
        # Bollinger Bands
        bb_position = indicators.get('bb_position', 0.5)
        if bb_position < 0.2:
            buy_signals += 1
        elif bb_position > 0.8:
            sell_signals += 1
        
        # Трендовые сигналы
        current_price = indicators.get('current_price', 0)
        ema_12 = indicators.get('ema_12', 0)
        ema_26 = indicators.get('ema_26', 0)
        
        if current_price > ema_12 > ema_26:
            buy_signals += 1
        elif current_price < ema_12 < ema_26:
            sell_signals += 1
        
        # Определяем финальный сигнал
        if buy_signals >= sell_signals + 2:
            return 'buy'
        elif sell_signals >= buy_signals + 2:
            return 'sell'
        else:
            return 'hold'
    
    def _calculate_optimal_levels(self, price: float, signal_direction: str, signal_quality: Dict) -> Dict:
        """Расчет оптимальных уровней входа и выхода"""
        
        # Базовые уровни стоп-лосса
        base_stop_loss_pct = self.stop_loss_levels
        
        # Корректируем стоп-лосс на основе качества сигнала
        quality_multiplier = 0.7 + (signal_quality['confidence'] * 0.6)  # 0.7-1.3
        stop_loss_pct = base_stop_loss_pct * quality_multiplier
        
        # Рассчитываем уровни
        if signal_direction == 'buy':
            stop_loss = price * (1 - stop_loss_pct)
            take_profit_1 = price * (1 + self.profit_targets[0])
            take_profit_2 = price * (1 + self.profit_targets[1])
            take_profit_3 = price * (1 + self.profit_targets[2])
        else:  # sell
            stop_loss = price * (1 + stop_loss_pct)
            take_profit_1 = price * (1 - self.profit_targets[0])
            take_profit_2 = price * (1 - self.profit_targets[1])
            take_profit_3 = price * (1 - self.profit_targets[2])
        
        # Рассчитываем соотношение риск/прибыль
        risk = abs(price - stop_loss)
        reward = abs(take_profit_1 - price)
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        # Определяем использование трейлинг стопа
        use_trailing_stop = (
            signal_quality['confidence'] > 0.7 and 
            self.optimization_mode != ProfitOptimizationMode.CONSERVATIVE
        )
        
        return {
            'stop_loss': stop_loss,
            'take_profit_1': take_profit_1,
            'take_profit_2': take_profit_2,
            'take_profit_3': take_profit_3,
            'risk_reward_ratio': risk_reward_ratio,
            'use_trailing_stop': use_trailing_stop,
            'stop_loss_pct': stop_loss_pct,
            'profit_targets': self.profit_targets
        }
    
    def _calculate_max_hold_time(self, signal_quality: Dict, market_regime: str) -> int:
        """Расчет максимального времени удержания позиции"""
        
        base_hours = {
            ProfitOptimizationMode.CONSERVATIVE: 48,  # 2 дня
            ProfitOptimizationMode.BALANCED: 72,      # 3 дня
            ProfitOptimizationMode.AGGRESSIVE: 96     # 4 дня
        }
        
        base_time = base_hours[self.optimization_mode]
        
        # Корректируем на основе качества сигнала
        quality_multiplier = 0.5 + signal_quality['confidence']  # 0.5-1.5
        
        # Корректируем на основе рыночного режима
        regime_multiplier = {
            'bull_trend': 1.2,
            'bear_trend': 1.2,
            'sideways': 0.8,
            'high_volatility': 0.6
        }.get(market_regime, 1.0)
        
        max_hours = int(base_time * quality_multiplier * regime_multiplier)
        return max(12, min(168, max_hours))  # От 12 часов до недели
    
    def get_optimization_stats(self) -> Dict:
        """Получение статистики оптимизации"""
        return {
            'optimization_mode': self.optimization_mode.value,
            'min_risk_reward_ratio': self.min_risk_reward_ratio,
            'profit_targets': self.profit_targets,
            'stop_loss_level': self.stop_loss_levels,
            'expected_win_rate': self._get_expected_win_rate(),
            'expected_profit_factor': self._get_expected_profit_factor()
        }
    
    def _get_expected_win_rate(self) -> float:
        """Ожидаемый винрейт для режима"""
        rates = {
            ProfitOptimizationMode.CONSERVATIVE: 0.45,  # 45%
            ProfitOptimizationMode.BALANCED: 0.40,      # 40%
            ProfitOptimizationMode.AGGRESSIVE: 0.35     # 35%
        }
        return rates[self.optimization_mode]
    
    def _get_expected_profit_factor(self) -> float:
        """Ожидаемый profit factor для режима"""
        factors = {
            ProfitOptimizationMode.CONSERVATIVE: 1.8,
            ProfitOptimizationMode.BALANCED: 2.2,
            ProfitOptimizationMode.AGGRESSIVE: 2.5
        }
        return factors[self.optimization_mode]

# Глобальные экземпляры для разных режимов
conservative_engine = ProfitableStrategyEngine(ProfitOptimizationMode.CONSERVATIVE)
balanced_engine = ProfitableStrategyEngine(ProfitOptimizationMode.BALANCED)
aggressive_engine = ProfitableStrategyEngine(ProfitOptimizationMode.AGGRESSIVE) 