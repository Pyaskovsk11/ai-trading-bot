"""
Extreme Profit Engine - Движок экстремально агрессивной стратегии
ЦЕЛЬ: 100% доходность за 2-4 недели
РИСК: ОЧЕНЬ ВЫСОКИЙ - только для опытных трейдеров!
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ExtremeMode(Enum):
    """Режимы экстремальной торговли"""
    TURBO = "turbo"           # 50% за неделю
    ROCKET = "rocket"         # 100% за 2 недели  
    NUCLEAR = "nuclear"       # 200% за месяц

@dataclass
class ExtremeSignal:
    """Экстремальный сигнал для максимальной прибыли"""
    signal: str                    # buy/sell/hold
    confidence: float              # 0.0-1.0
    entry_price: float
    leverage: float                # Плечо 1x-10x
    position_size: float           # 20-50% капитала
    stop_loss: float
    take_profit_1: float           # 10-20%
    take_profit_2: float           # 20-40%
    take_profit_3: float           # 40-80%
    trailing_stop: bool
    max_hold_time: int             # 2-24 часа
    risk_reward_ratio: float       # Минимум 1:5
    volatility_target: float       # Целевая волатильность
    momentum_strength: float       # Сила моментума
    strategy_type: str
    reason: str
    metadata: Dict

class ExtremeProfitEngine:
    """
    Движок экстремально агрессивной стратегии для достижения 100%+ доходности
    ⚠️ ВНИМАНИЕ: ОЧЕНЬ ВЫСОКИЙ РИСК!
    """
    
    def __init__(self, extreme_mode: ExtremeMode = ExtremeMode.ROCKET):
        self.extreme_mode = extreme_mode
        self.min_risk_reward_ratio = self._get_min_risk_reward_ratio()
        self.position_sizes = self._get_position_sizes()
        self.leverage_levels = self._get_leverage_levels()
        self.profit_targets = self._get_profit_targets()
        self.volatility_threshold = self._get_volatility_threshold()
        
        logger.warning(f"🚨 ExtremeProfitEngine инициализирован в режиме {extreme_mode.value}")
        logger.warning("⚠️ ВНИМАНИЕ: ЭКСТРЕМАЛЬНО ВЫСОКИЙ РИСК!")
    
    def _get_min_risk_reward_ratio(self) -> float:
        """Минимальное соотношение риск/прибыль для экстремальных режимов"""
        ratios = {
            ExtremeMode.TURBO: 3.0,     # 1:3 минимум
            ExtremeMode.ROCKET: 5.0,    # 1:5 минимум
            ExtremeMode.NUCLEAR: 8.0    # 1:8 минимум
        }
        return ratios[self.extreme_mode]
    
    def _get_position_sizes(self) -> List[float]:
        """Размеры позиций для экстремальных режимов"""
        sizes = {
            ExtremeMode.TURBO: [0.20, 0.30, 0.40],      # 20-40% капитала
            ExtremeMode.ROCKET: [0.30, 0.40, 0.50],     # 30-50% капитала
            ExtremeMode.NUCLEAR: [0.40, 0.60, 0.80]     # 40-80% капитала
        }
        return sizes[self.extreme_mode]
    
    def _get_leverage_levels(self) -> List[float]:
        """Уровни плеча для экстремальных режимов"""
        leverage = {
            ExtremeMode.TURBO: [2.0, 3.0, 5.0],        # 2x-5x плечо
            ExtremeMode.ROCKET: [3.0, 5.0, 8.0],       # 3x-8x плечо
            ExtremeMode.NUCLEAR: [5.0, 8.0, 10.0]      # 5x-10x плечо
        }
        return leverage[self.extreme_mode]
    
    def _get_profit_targets(self) -> List[float]:
        """Целевые уровни прибыли для экстремальных режимов"""
        targets = {
            ExtremeMode.TURBO: [0.10, 0.20, 0.35],     # 10%, 20%, 35%
            ExtremeMode.ROCKET: [0.15, 0.30, 0.50],    # 15%, 30%, 50%
            ExtremeMode.NUCLEAR: [0.25, 0.50, 0.80]    # 25%, 50%, 80%
        }
        return targets[self.extreme_mode]
    
    def _get_volatility_threshold(self) -> float:
        """Минимальная волатильность для входа"""
        thresholds = {
            ExtremeMode.TURBO: 0.03,      # 3% минимум
            ExtremeMode.ROCKET: 0.05,     # 5% минимум
            ExtremeMode.NUCLEAR: 0.08     # 8% минимум
        }
        return thresholds[self.extreme_mode]
    
    async def analyze_extreme_signal(self, 
                                   indicators: Dict, 
                                   market_regime: str, 
                                   price: float, 
                                   timestamp: datetime,
                                   volume_profile: Dict = None,
                                   news_sentiment: float = 0.0) -> Optional[ExtremeSignal]:
        """
        Анализ экстремального сигнала для максимальной прибыли
        """
        try:
            # 1. Проверяем базовые условия для экстремальной торговли
            if not self._check_extreme_conditions(indicators, market_regime):
                return None
            
            # 2. Оценка экстремального потенциала
            extreme_score = self._assess_extreme_potential(indicators, market_regime, volume_profile, news_sentiment)
            
            if extreme_score['score'] < 80:  # Очень высокий порог
                return None
            
            # 3. Определяем направление экстремального движения
            signal_direction = self._determine_extreme_direction(indicators, market_regime, news_sentiment)
            
            if signal_direction == 'hold':
                return None
            
            # 4. Рассчитываем экстремальные уровни
            levels = self._calculate_extreme_levels(price, signal_direction, extreme_score)
            
            # 5. Проверяем соотношение риск/прибыль
            if levels['risk_reward_ratio'] < self.min_risk_reward_ratio:
                logger.debug(f"Экстремальный сигнал отклонен: низкое R/R {levels['risk_reward_ratio']:.2f}")
                return None
            
            # 6. Определяем размер позиции и плечо
            position_params = self._calculate_position_parameters(extreme_score, levels)
            
            # 7. Рассчитываем время удержания
            max_hold_time = self._calculate_extreme_hold_time(extreme_score, market_regime)
            
            # 8. Создаем экстремальный сигнал
            extreme_signal = ExtremeSignal(
                signal=signal_direction,
                confidence=extreme_score['confidence'],
                entry_price=price,
                leverage=position_params['leverage'],
                position_size=position_params['position_size'],
                stop_loss=levels['stop_loss'],
                take_profit_1=levels['take_profit_1'],
                take_profit_2=levels['take_profit_2'],
                take_profit_3=levels['take_profit_3'],
                trailing_stop=True,  # Всегда используем трейлинг
                max_hold_time=max_hold_time,
                risk_reward_ratio=levels['risk_reward_ratio'],
                volatility_target=indicators.get('volatility', 0.05),
                momentum_strength=extreme_score['momentum'],
                strategy_type=f"extreme_{self.extreme_mode.value}",
                reason=extreme_score['reason'],
                metadata={
                    'extreme_score': extreme_score,
                    'market_regime': market_regime,
                    'extreme_mode': self.extreme_mode.value,
                    'position_params': position_params,
                    'expected_profit': levels['expected_profit'],
                    'max_risk': levels['max_risk'],
                    'confidence_factors': extreme_score['factors']
                }
            )
            
            logger.warning(f"🚨 ЭКСТРЕМАЛЬНЫЙ СИГНАЛ: {signal_direction} @ ${price:.2f}")
            logger.warning(f"💰 Ожидаемая прибыль: {levels['expected_profit']:.1f}%")
            logger.warning(f"⚠️ Максимальный риск: {levels['max_risk']:.1f}%")
            logger.warning(f"🎯 R/R: {levels['risk_reward_ratio']:.1f}")
            logger.warning(f"📊 Плечо: {position_params['leverage']:.1f}x")
            
            return extreme_signal
            
        except Exception as e:
            logger.error(f"Ошибка анализа экстремального сигнала: {e}")
            return None
    
    def _check_extreme_conditions(self, indicators: Dict, market_regime: str) -> bool:
        """Проверка базовых условий для экстремальной торговли"""
        
        # 1. Минимальная волатильность
        volatility = indicators.get('volatility', 0.01)
        if volatility < self.volatility_threshold:
            return False
        
        # 2. Достаточный объем
        volume_ratio = indicators.get('volume_ratio', 0.5)
        if volume_ratio < 1.5:  # Минимум 1.5x средний объем
            return False
        
        # 3. Подходящий рыночный режим
        if market_regime in ['low_volatility', 'sideways_tight']:
            return False
        
        # 4. Технические условия
        rsi = indicators.get('rsi', 50)
        if 40 <= rsi <= 60:  # Избегаем нейтральной зоны
            return False
        
        return True
    
    def _assess_extreme_potential(self, indicators: Dict, market_regime: str, 
                                volume_profile: Dict = None, news_sentiment: float = 0.0) -> Dict:
        """Оценка экстремального потенциала для максимальной прибыли"""
        
        extreme_score = 0
        momentum_score = 0
        confidence_factors = []
        
        # 1. RSI экстремальные уровни (25 баллов)
        rsi = indicators.get('rsi', 50)
        if rsi <= 20:  # Экстремальная перепроданность
            extreme_score += 25
            momentum_score += 30
            confidence_factors.append(f"RSI экстремальная перепроданность ({rsi:.1f})")
        elif rsi >= 80:  # Экстремальная перекупленность
            extreme_score += 25
            momentum_score += 30
            confidence_factors.append(f"RSI экстремальная перекупленность ({rsi:.1f})")
        elif rsi <= 25 or rsi >= 75:
            extreme_score += 15
            momentum_score += 20
            confidence_factors.append(f"RSI сильный уровень ({rsi:.1f})")
        
        # 2. MACD экстремальные сигналы (30 баллов)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_histogram = indicators.get('macd_histogram', 0)
        prev_histogram = indicators.get('prev_macd_histogram', 0)
        
        # Сильное ускорение MACD
        histogram_acceleration = abs(macd_histogram - prev_histogram)
        if histogram_acceleration > 0.001:  # Сильное ускорение
            if macd > macd_signal and macd_histogram > prev_histogram:
                extreme_score += 30
                momentum_score += 40
                confidence_factors.append("MACD экстремальное бычье ускорение")
            elif macd < macd_signal and macd_histogram < prev_histogram:
                extreme_score += 30
                momentum_score += 40
                confidence_factors.append("MACD экстремальное медвежье ускорение")
        
        # 3. Bollinger Bands прорывы (20 баллов)
        bb_position = indicators.get('bb_position', 0.5)
        bb_width = indicators.get('bb_width', 0.04)
        
        if bb_width > 0.06:  # Широкие полосы = высокая волатильность
            if bb_position < 0.05:  # Прорыв нижней границы
                extreme_score += 20
                momentum_score += 25
                confidence_factors.append("Прорыв нижней границы BB при высокой волатильности")
            elif bb_position > 0.95:  # Прорыв верхней границы
                extreme_score += 20
                momentum_score += 25
                confidence_factors.append("Прорыв верхней границы BB при высокой волатильности")
        
        # 4. Экстремальная волатильность (15 баллов)
        volatility = indicators.get('volatility', 0.02)
        if volatility > 0.08:  # Очень высокая волатильность
            extreme_score += 15
            momentum_score += 20
            confidence_factors.append(f"Экстремальная волатильность ({volatility:.3f})")
        elif volatility > 0.05:
            extreme_score += 10
            momentum_score += 15
            confidence_factors.append(f"Высокая волатильность ({volatility:.3f})")
        
        # 5. Объемные всплески (15 баллов)
        volume_ratio = indicators.get('volume_ratio', 1.0)
        if volume_ratio > 3.0:  # Экстремальный объем
            extreme_score += 15
            momentum_score += 20
            confidence_factors.append(f"Экстремальный объем ({volume_ratio:.1f}x)")
        elif volume_ratio > 2.0:
            extreme_score += 10
            momentum_score += 15
            confidence_factors.append(f"Очень высокий объем ({volume_ratio:.1f}x)")
        
        # 6. Трендовая сила (10 баллов)
        current_price = indicators.get('current_price', 0)
        ema_12 = indicators.get('ema_12', 0)
        ema_26 = indicators.get('ema_26', 0)
        sma_50 = indicators.get('sma_50', 0)
        
        # Экстремальное расхождение EMA
        if current_price > 0 and ema_12 > 0:
            price_ema_diff = abs(current_price - ema_12) / current_price
            if price_ema_diff > 0.05:  # 5%+ расхождение
                extreme_score += 10
                momentum_score += 15
                confidence_factors.append(f"Экстремальное расхождение с EMA ({price_ema_diff:.1%})")
        
        # 7. Новостной сентимент (бонус 10 баллов)
        if abs(news_sentiment) > 0.7:  # Сильный новостной фон
            extreme_score += 10
            momentum_score += 10
            confidence_factors.append(f"Сильный новостной сентимент ({news_sentiment:.2f})")
        
        # 8. Рыночный режим (бонус/штраф)
        regime_multiplier = {
            'bull_breakout': 1.2,
            'bear_breakout': 1.2,
            'high_volatility': 1.1,
            'news_driven': 1.15,
            'sideways': 0.7,
            'low_volatility': 0.5
        }.get(market_regime, 1.0)
        
        extreme_score = int(extreme_score * regime_multiplier)
        momentum_score = int(momentum_score * regime_multiplier)
        
        # Нормализация
        extreme_score = max(0, min(100, extreme_score))
        momentum_score = max(0, min(100, momentum_score))
        confidence = extreme_score / 100.0
        
        return {
            'score': extreme_score,
            'momentum': momentum_score,
            'confidence': confidence,
            'reason': f"ЭКСТРЕМАЛЬНЫЙ ПОТЕНЦИАЛ ({extreme_score}): " + "; ".join(confidence_factors[:3]),
            'factors': confidence_factors,
            'regime_multiplier': regime_multiplier
        }
    
    def _determine_extreme_direction(self, indicators: Dict, market_regime: str, news_sentiment: float = 0.0) -> str:
        """Определение направления экстремального движения"""
        
        buy_signals = 0
        sell_signals = 0
        
        # RSI экстремальные уровни
        rsi = indicators.get('rsi', 50)
        if rsi <= 25:
            buy_signals += 4
        elif rsi >= 75:
            sell_signals += 4
        
        # MACD ускорение
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_histogram = indicators.get('macd_histogram', 0)
        prev_histogram = indicators.get('prev_macd_histogram', 0)
        
        if macd > macd_signal and macd_histogram > prev_histogram:
            buy_signals += 3
        elif macd < macd_signal and macd_histogram < prev_histogram:
            sell_signals += 3
        
        # Bollinger Bands прорывы
        bb_position = indicators.get('bb_position', 0.5)
        if bb_position < 0.1:
            buy_signals += 2
        elif bb_position > 0.9:
            sell_signals += 2
        
        # Трендовое направление
        current_price = indicators.get('current_price', 0)
        ema_12 = indicators.get('ema_12', 0)
        ema_26 = indicators.get('ema_26', 0)
        
        if current_price > ema_12 > ema_26:
            buy_signals += 2
        elif current_price < ema_12 < ema_26:
            sell_signals += 2
        
        # Новостной сентимент
        if news_sentiment > 0.5:
            buy_signals += 1
        elif news_sentiment < -0.5:
            sell_signals += 1
        
        # Требуем очень сильное преимущество для экстремальной торговли
        if buy_signals >= sell_signals + 4:
            return 'buy'
        elif sell_signals >= buy_signals + 4:
            return 'sell'
        else:
            return 'hold'
    
    def _calculate_extreme_levels(self, price: float, signal_direction: str, extreme_score: Dict) -> Dict:
        """Расчет экстремальных уровней входа и выхода"""
        
        # Адаптивные уровни на основе экстремального потенциала
        score_multiplier = 0.8 + (extreme_score['confidence'] * 0.4)  # 0.8-1.2
        momentum_multiplier = 0.9 + (extreme_score['momentum'] / 100.0 * 0.3)  # 0.9-1.2
        
        # Базовые уровни для экстремальной торговли
        base_stop_loss_pct = 0.03  # 3% стоп-лосс (выше из-за волатильности)
        
        # Корректируем стоп-лосс
        stop_loss_pct = base_stop_loss_pct * score_multiplier
        
        # Экстремальные тейк-профиты
        profit_targets = [
            self.profit_targets[0] * momentum_multiplier,  # Первый уровень
            self.profit_targets[1] * momentum_multiplier,  # Второй уровень  
            self.profit_targets[2] * momentum_multiplier   # Третий уровень
        ]
        
        if signal_direction == 'buy':
            stop_loss = price * (1 - stop_loss_pct)
            take_profit_1 = price * (1 + profit_targets[0])
            take_profit_2 = price * (1 + profit_targets[1])
            take_profit_3 = price * (1 + profit_targets[2])
        else:  # sell
            stop_loss = price * (1 + stop_loss_pct)
            take_profit_1 = price * (1 - profit_targets[0])
            take_profit_2 = price * (1 - profit_targets[1])
            take_profit_3 = price * (1 - profit_targets[2])
        
        # Рассчитываем соотношение риск/прибыль
        risk = abs(price - stop_loss)
        reward = abs(take_profit_1 - price)
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        # Ожидаемая прибыль и риск
        expected_profit = profit_targets[0] * 100  # В процентах
        max_risk = stop_loss_pct * 100
        
        return {
            'stop_loss': stop_loss,
            'take_profit_1': take_profit_1,
            'take_profit_2': take_profit_2,
            'take_profit_3': take_profit_3,
            'risk_reward_ratio': risk_reward_ratio,
            'expected_profit': expected_profit,
            'max_risk': max_risk,
            'profit_targets': profit_targets,
            'stop_loss_pct': stop_loss_pct
        }
    
    def _calculate_position_parameters(self, extreme_score: Dict, levels: Dict) -> Dict:
        """Расчет параметров позиции (размер и плечо)"""
        
        # Размер позиции на основе уверенности
        confidence = extreme_score['confidence']
        momentum = extreme_score['momentum'] / 100.0
        
        # Выбираем размер позиции
        if confidence > 0.9 and momentum > 0.8:
            position_size = self.position_sizes[2]  # Максимальный размер
            leverage = self.leverage_levels[2]      # Максимальное плечо
        elif confidence > 0.8 and momentum > 0.6:
            position_size = self.position_sizes[1]  # Средний размер
            leverage = self.leverage_levels[1]      # Среднее плечо
        else:
            position_size = self.position_sizes[0]  # Минимальный размер
            leverage = self.leverage_levels[0]      # Минимальное плечо
        
        # Корректируем на основе соотношения риск/прибыль
        rr_ratio = levels['risk_reward_ratio']
        if rr_ratio > 8.0:  # Очень хорошее соотношение
            position_size *= 1.2
            leverage *= 1.1
        elif rr_ratio > 6.0:
            position_size *= 1.1
        
        # Ограничения безопасности
        position_size = min(position_size, 0.8)  # Максимум 80% капитала
        leverage = min(leverage, 10.0)           # Максимум 10x плечо
        
        return {
            'position_size': position_size,
            'leverage': leverage,
            'effective_exposure': position_size * leverage  # Реальная экспозиция
        }
    
    def _calculate_extreme_hold_time(self, extreme_score: Dict, market_regime: str) -> int:
        """Расчет времени удержания экстремальной позиции"""
        
        base_hours = {
            ExtremeMode.TURBO: 6,      # 6 часов
            ExtremeMode.ROCKET: 4,     # 4 часа
            ExtremeMode.NUCLEAR: 2     # 2 часа
        }
        
        base_time = base_hours[self.extreme_mode]
        
        # Корректируем на основе моментума
        momentum_multiplier = 0.5 + (extreme_score['momentum'] / 100.0)  # 0.5-1.5
        
        # Корректируем на основе рыночного режима
        regime_multiplier = {
            'bull_breakout': 1.5,
            'bear_breakout': 1.5,
            'high_volatility': 0.8,
            'news_driven': 0.6
        }.get(market_regime, 1.0)
        
        max_hours = int(base_time * momentum_multiplier * regime_multiplier)
        return max(1, min(24, max_hours))  # От 1 часа до суток
    
    def get_extreme_stats(self) -> Dict:
        """Получение статистики экстремального режима"""
        return {
            'extreme_mode': self.extreme_mode.value,
            'target_weekly_return': self._get_target_weekly_return(),
            'min_risk_reward_ratio': self.min_risk_reward_ratio,
            'position_sizes': self.position_sizes,
            'leverage_levels': self.leverage_levels,
            'profit_targets': self.profit_targets,
            'volatility_threshold': self.volatility_threshold,
            'expected_win_rate': self._get_expected_win_rate(),
            'max_drawdown_risk': self._get_max_drawdown_risk(),
            'warning': "⚠️ ЭКСТРЕМАЛЬНО ВЫСОКИЙ РИСК!"
        }
    
    def _get_target_weekly_return(self) -> float:
        """Целевая недельная доходность"""
        targets = {
            ExtremeMode.TURBO: 0.50,     # 50% в неделю
            ExtremeMode.ROCKET: 0.75,    # 75% в неделю (100% за 2 недели)
            ExtremeMode.NUCLEAR: 1.00    # 100% в неделю
        }
        return targets[self.extreme_mode]
    
    def _get_expected_win_rate(self) -> float:
        """Ожидаемый винрейт для экстремального режима"""
        rates = {
            ExtremeMode.TURBO: 0.40,     # 40%
            ExtremeMode.ROCKET: 0.35,    # 35%
            ExtremeMode.NUCLEAR: 0.30    # 30%
        }
        return rates[self.extreme_mode]
    
    def _get_max_drawdown_risk(self) -> float:
        """Максимальный риск просадки"""
        risks = {
            ExtremeMode.TURBO: 0.30,     # 30%
            ExtremeMode.ROCKET: 0.50,    # 50%
            ExtremeMode.NUCLEAR: 0.70    # 70%
        }
        return risks[self.extreme_mode]

# Глобальные экземпляры для разных экстремальных режимов
turbo_engine = ExtremeProfitEngine(ExtremeMode.TURBO)
rocket_engine = ExtremeProfitEngine(ExtremeMode.ROCKET)
nuclear_engine = ExtremeProfitEngine(ExtremeMode.NUCLEAR) 