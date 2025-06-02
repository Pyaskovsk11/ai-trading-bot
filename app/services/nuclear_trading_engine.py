"""
NUCLEAR Trading Engine - Экстремально агрессивная торговля для 100% доходности
⚠️ КРИТИЧЕСКИ ВЫСОКИЙ РИСК! Только для опытных трейдеров!
ЦЕЛЬ: 100% доходность за 2-4 недели
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import json

logger = logging.getLogger(__name__)

class NuclearMode(Enum):
    """Режимы NUCLEAR торговли"""
    FUSION = "fusion"         # 200% за месяц
    FISSION = "fission"       # 500% за месяц  
    ANTIMATTER = "antimatter" # 1000% за месяц (ЭКСТРЕМАЛЬНО ОПАСНО!)

@dataclass
class NuclearSignal:
    """Ядерный сигнал для экстремальной прибыли"""
    signal: str                    # buy/sell/hold
    confidence: float              # 0.95-1.0 (только высочайшая уверенность)
    entry_price: float
    leverage: float                # 10x-50x плечо
    position_size: float           # 50-95% капитала
    stop_loss: float
    take_profit_1: float           # 25-50%
    take_profit_2: float           # 50-100%
    take_profit_3: float           # 100-200%
    trailing_stop: bool
    max_hold_time: int             # 30 минут - 4 часа
    risk_reward_ratio: float       # Минимум 1:10
    volatility_target: float       # Целевая волатильность >20%
    momentum_strength: float       # Сила моментума >90
    strategy_type: str
    reason: str
    nuclear_score: float           # 95-100 баллов
    metadata: Dict

class NuclearTradingEngine:
    """
    NUCLEAR Trading Engine - Экстремально агрессивная торговля
    ⚠️ ВНИМАНИЕ: КРИТИЧЕСКИ ВЫСОКИЙ РИСК ПОЛНОЙ ПОТЕРИ КАПИТАЛА!
    """
    
    def __init__(self, nuclear_mode: NuclearMode = NuclearMode.FUSION):
        self.nuclear_mode = nuclear_mode
        self.min_nuclear_score = self._get_min_nuclear_score()
        self.min_risk_reward_ratio = self._get_min_risk_reward_ratio()
        self.position_sizes = self._get_position_sizes()
        self.leverage_levels = self._get_leverage_levels()
        self.profit_targets = self._get_profit_targets()
        self.volatility_threshold = self._get_volatility_threshold()
        self.confidence_threshold = self._get_confidence_threshold()
        
        logger.warning(f"🚨 NUCLEAR Trading Engine активирован в режиме {nuclear_mode.value}")
        logger.warning("⚠️ КРИТИЧЕСКИ ВЫСОКИЙ РИСК ПОЛНОЙ ПОТЕРИ КАПИТАЛА!")
    
    def _get_min_nuclear_score(self) -> float:
        """Минимальный ядерный счет для входа"""
        scores = {
            NuclearMode.FUSION: 95.0,      # Топ 5% сигналов
            NuclearMode.FISSION: 97.0,     # Топ 3% сигналов
            NuclearMode.ANTIMATTER: 99.0   # Топ 1% сигналов
        }
        return scores[self.nuclear_mode]
    
    def _get_min_risk_reward_ratio(self) -> float:
        """Минимальное соотношение риск/прибыль"""
        ratios = {
            NuclearMode.FUSION: 10.0,      # 1:10 минимум
            NuclearMode.FISSION: 15.0,     # 1:15 минимум
            NuclearMode.ANTIMATTER: 20.0   # 1:20 минимум
        }
        return ratios[self.nuclear_mode]
    
    def _get_position_sizes(self) -> List[float]:
        """Размеры позиций для ядерных режимов"""
        sizes = {
            NuclearMode.FUSION: [0.50, 0.70, 0.80],        # 50-80% капитала
            NuclearMode.FISSION: [0.70, 0.85, 0.95],       # 70-95% капитала
            NuclearMode.ANTIMATTER: [0.90, 0.95, 0.99]     # 90-99% капитала
        }
        return sizes[self.nuclear_mode]
    
    def _get_leverage_levels(self) -> List[float]:
        """Уровни плеча для ядерных режимов"""
        leverage = {
            NuclearMode.FUSION: [10.0, 20.0, 30.0],        # 10x-30x плечо
            NuclearMode.FISSION: [20.0, 35.0, 50.0],       # 20x-50x плечо
            NuclearMode.ANTIMATTER: [30.0, 50.0, 100.0]    # 30x-100x плечо
        }
        return leverage[self.nuclear_mode]
    
    def _get_profit_targets(self) -> List[float]:
        """Целевые уровни прибыли"""
        targets = {
            NuclearMode.FUSION: [0.25, 0.50, 1.00],        # 25%, 50%, 100%
            NuclearMode.FISSION: [0.50, 1.00, 2.00],       # 50%, 100%, 200%
            NuclearMode.ANTIMATTER: [1.00, 2.00, 5.00]     # 100%, 200%, 500%
        }
        return targets[self.nuclear_mode]
    
    def _get_volatility_threshold(self) -> float:
        """Минимальная волатильность для входа"""
        thresholds = {
            NuclearMode.FUSION: 0.15,      # 15% минимум
            NuclearMode.FISSION: 0.20,     # 20% минимум
            NuclearMode.ANTIMATTER: 0.30   # 30% минимум
        }
        return thresholds[self.nuclear_mode]
    
    def _get_confidence_threshold(self) -> float:
        """Минимальная уверенность для входа"""
        thresholds = {
            NuclearMode.FUSION: 0.95,      # 95% минимум
            NuclearMode.FISSION: 0.97,     # 97% минимум
            NuclearMode.ANTIMATTER: 0.99   # 99% минимум
        }
        return thresholds[self.nuclear_mode]
    
    async def analyze_nuclear_signal(self, 
                                   indicators: Dict, 
                                   market_regime: str, 
                                   price: float, 
                                   timestamp: datetime,
                                   volume_profile: Dict = None,
                                   news_sentiment: float = 0.0,
                                   social_sentiment: float = 0.0,
                                   whale_activity: float = 0.0) -> Optional[NuclearSignal]:
        """
        Анализ ядерного сигнала для экстремальной прибыли
        """
        try:
            # 1. Проверяем базовые условия для ядерной торговли
            if not self._check_nuclear_conditions(indicators, market_regime):
                return None
            
            # 2. Оценка ядерного потенциала (100-балльная система)
            nuclear_analysis = self._assess_nuclear_potential(
                indicators, market_regime, volume_profile, 
                news_sentiment, social_sentiment, whale_activity
            )
            
            if nuclear_analysis['nuclear_score'] < self.min_nuclear_score:
                logger.debug(f"Ядерный сигнал отклонен: низкий счет {nuclear_analysis['nuclear_score']:.1f}")
                return None
            
            # 3. Определяем направление ядерного взрыва
            signal_direction = self._determine_nuclear_direction(
                indicators, market_regime, news_sentiment, social_sentiment
            )
            
            if signal_direction == 'hold':
                return None
            
            # 4. Рассчитываем ядерные уровни
            levels = self._calculate_nuclear_levels(price, signal_direction, nuclear_analysis)
            
            # 5. Проверяем соотношение риск/прибыль
            if levels['risk_reward_ratio'] < self.min_risk_reward_ratio:
                logger.debug(f"Ядерный сигнал отклонен: низкое R/R {levels['risk_reward_ratio']:.2f}")
                return None
            
            # 6. Определяем размер позиции и плечо
            position_params = self._calculate_nuclear_position_parameters(nuclear_analysis, levels)
            
            # 7. Рассчитываем время удержания
            max_hold_time = self._calculate_nuclear_hold_time(nuclear_analysis, market_regime)
            
            # 8. Создаем ядерный сигнал
            nuclear_signal = NuclearSignal(
                signal=signal_direction,
                confidence=nuclear_analysis['confidence'],
                entry_price=price,
                leverage=position_params['leverage'],
                position_size=position_params['position_size'],
                stop_loss=levels['stop_loss'],
                take_profit_1=levels['take_profit_1'],
                take_profit_2=levels['take_profit_2'],
                take_profit_3=levels['take_profit_3'],
                trailing_stop=True,
                max_hold_time=max_hold_time,
                risk_reward_ratio=levels['risk_reward_ratio'],
                volatility_target=indicators.get('volatility', 0.20),
                momentum_strength=nuclear_analysis['momentum'],
                strategy_type=f"nuclear_{self.nuclear_mode.value}",
                reason=nuclear_analysis['reason'],
                nuclear_score=nuclear_analysis['nuclear_score'],
                metadata={
                    'nuclear_analysis': nuclear_analysis,
                    'market_regime': market_regime,
                    'nuclear_mode': self.nuclear_mode.value,
                    'position_params': position_params,
                    'expected_profit': levels['expected_profit'],
                    'max_risk': levels['max_risk'],
                    'confidence_factors': nuclear_analysis['factors'],
                    'timestamp': timestamp.isoformat()  # Исправление ошибки timestamp
                }
            )
            
            logger.warning(f"☢️ ЯДЕРНЫЙ СИГНАЛ: {signal_direction} @ ${price:.2f}")
            logger.warning(f"💥 Ядерный счет: {nuclear_analysis['nuclear_score']:.1f}/100")
            logger.warning(f"💰 Ожидаемая прибыль: {levels['expected_profit']:.1f}%")
            logger.warning(f"⚠️ Максимальный риск: {levels['max_risk']:.1f}%")
            logger.warning(f"🎯 R/R: {levels['risk_reward_ratio']:.1f}")
            logger.warning(f"📊 Плечо: {position_params['leverage']:.1f}x")
            logger.warning(f"💣 Размер позиции: {position_params['position_size']:.1%}")
            
            return nuclear_signal
            
        except Exception as e:
            logger.error(f"Ошибка анализа ядерного сигнала: {e}")
            return None
    
    def _check_nuclear_conditions(self, indicators: Dict, market_regime: str) -> bool:
        """Проверка базовых условий для ядерной торговли"""
        
        # 1. Экстремальная волатильность
        volatility = indicators.get('volatility', 0.01)
        if volatility < self.volatility_threshold:
            return False
        
        # 2. Массивный объем
        volume_ratio = indicators.get('volume_ratio', 0.5)
        if volume_ratio < 3.0:  # Минимум 3x средний объем
            return False
        
        # 3. Подходящий рыночный режим
        if market_regime in ['low_volatility', 'sideways_tight', 'consolidation']:
            return False
        
        # 4. Экстремальные технические условия
        rsi = indicators.get('rsi', 50)
        if 30 <= rsi <= 70:  # Только экстремальные уровни
            return False
        
        # 5. MACD экстремальное ускорение
        macd_histogram = indicators.get('macd_histogram', 0)
        prev_histogram = indicators.get('prev_macd_histogram', 0)
        histogram_acceleration = abs(macd_histogram - prev_histogram)
        if histogram_acceleration < 0.002:  # Очень сильное ускорение
            return False
        
        return True
    
    def _assess_nuclear_potential(self, indicators: Dict, market_regime: str, 
                                volume_profile: Dict = None, news_sentiment: float = 0.0,
                                social_sentiment: float = 0.0, whale_activity: float = 0.0) -> Dict:
        """Оценка ядерного потенциала (100-балльная система)"""
        
        nuclear_score = 0
        momentum_score = 0
        confidence_factors = []
        
        # 1. RSI экстремальные уровни (20 баллов)
        rsi = indicators.get('rsi', 50)
        if rsi <= 15:  # Критическая перепроданность
            nuclear_score += 20
            momentum_score += 25
            confidence_factors.append(f"RSI критическая перепроданность ({rsi:.1f})")
        elif rsi >= 85:  # Критическая перекупленность
            nuclear_score += 20
            momentum_score += 25
            confidence_factors.append(f"RSI критическая перекупленность ({rsi:.1f})")
        elif rsi <= 20 or rsi >= 80:
            nuclear_score += 15
            momentum_score += 20
            confidence_factors.append(f"RSI экстремальный уровень ({rsi:.1f})")
        
        # 2. MACD ядерное ускорение (25 баллов)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_histogram = indicators.get('macd_histogram', 0)
        prev_histogram = indicators.get('prev_macd_histogram', 0)
        
        histogram_acceleration = abs(macd_histogram - prev_histogram)
        if histogram_acceleration > 0.005:  # Ядерное ускорение
            if macd > macd_signal and macd_histogram > prev_histogram:
                nuclear_score += 25
                momentum_score += 30
                confidence_factors.append("MACD ядерное бычье ускорение")
            elif macd < macd_signal and macd_histogram < prev_histogram:
                nuclear_score += 25
                momentum_score += 30
                confidence_factors.append("MACD ядерное медвежье ускорение")
        elif histogram_acceleration > 0.003:
            nuclear_score += 15
            momentum_score += 20
            confidence_factors.append("MACD сильное ускорение")
        
        # 3. Bollinger Bands ядерные прорывы (15 баллов)
        bb_position = indicators.get('bb_position', 0.5)
        bb_width = indicators.get('bb_width', 0.04)
        
        if bb_width > 0.15:  # Экстремально широкие полосы
            if bb_position < 0.02:  # Ядерный прорыв вниз
                nuclear_score += 15
                momentum_score += 20
                confidence_factors.append("Ядерный прорыв нижней границы BB")
            elif bb_position > 0.98:  # Ядерный прорыв вверх
                nuclear_score += 15
                momentum_score += 20
                confidence_factors.append("Ядерный прорыв верхней границы BB")
        
        # 4. Ядерная волатильность (15 баллов)
        volatility = indicators.get('volatility', 0.02)
        if volatility > 0.25:  # Ядерная волатильность
            nuclear_score += 15
            momentum_score += 20
            confidence_factors.append(f"Ядерная волатильность ({volatility:.3f})")
        elif volatility > 0.15:
            nuclear_score += 10
            momentum_score += 15
            confidence_factors.append(f"Экстремальная волатильность ({volatility:.3f})")
        
        # 5. Объемные ядерные взрывы (15 баллов)
        volume_ratio = indicators.get('volume_ratio', 1.0)
        if volume_ratio > 10.0:  # Ядерный объем
            nuclear_score += 15
            momentum_score += 20
            confidence_factors.append(f"Ядерный объем ({volume_ratio:.1f}x)")
        elif volume_ratio > 5.0:
            nuclear_score += 10
            momentum_score += 15
            confidence_factors.append(f"Экстремальный объем ({volume_ratio:.1f}x)")
        
        # 6. Новостной ядерный сентимент (10 баллов)
        if abs(news_sentiment) > 0.8:  # Ядерные новости
            nuclear_score += 10
            momentum_score += 15
            confidence_factors.append(f"Ядерный новостной сентимент ({news_sentiment:.2f})")
        elif abs(news_sentiment) > 0.6:
            nuclear_score += 5
            momentum_score += 10
            confidence_factors.append(f"Сильный новостной сентимент ({news_sentiment:.2f})")
        
        # 7. Социальный ядерный сентимент (бонус 5 баллов)
        if abs(social_sentiment) > 0.8:
            nuclear_score += 5
            momentum_score += 10
            confidence_factors.append(f"Ядерный социальный сентимент ({social_sentiment:.2f})")
        
        # 8. Активность китов (бонус 5 баллов)
        if whale_activity > 0.8:
            nuclear_score += 5
            momentum_score += 10
            confidence_factors.append(f"Экстремальная активность китов ({whale_activity:.2f})")
        
        # 9. Рыночный режим (множитель)
        regime_multiplier = {
            'nuclear_breakout': 1.3,
            'extreme_volatility': 1.2,
            'news_explosion': 1.25,
            'whale_movement': 1.15,
            'flash_crash': 1.2,
            'parabolic_move': 1.3
        }.get(market_regime, 1.0)
        
        nuclear_score = int(nuclear_score * regime_multiplier)
        momentum_score = int(momentum_score * regime_multiplier)
        
        # Нормализация
        nuclear_score = max(0, min(100, nuclear_score))
        momentum_score = max(0, min(100, momentum_score))
        confidence = nuclear_score / 100.0
        
        return {
            'nuclear_score': nuclear_score,
            'momentum': momentum_score,
            'confidence': confidence,
            'reason': f"ЯДЕРНЫЙ ПОТЕНЦИАЛ ({nuclear_score}): " + "; ".join(confidence_factors[:3]),
            'factors': confidence_factors,
            'regime_multiplier': regime_multiplier
        }
    
    def _determine_nuclear_direction(self, indicators: Dict, market_regime: str, 
                                   news_sentiment: float = 0.0, social_sentiment: float = 0.0) -> str:
        """Определение направления ядерного взрыва"""
        
        buy_signals = 0
        sell_signals = 0
        
        # RSI экстремальные уровни (вес 5)
        rsi = indicators.get('rsi', 50)
        if rsi <= 20:
            buy_signals += 5
        elif rsi >= 80:
            sell_signals += 5
        
        # MACD ядерное ускорение (вес 4)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_histogram = indicators.get('macd_histogram', 0)
        prev_histogram = indicators.get('prev_macd_histogram', 0)
        
        if macd > macd_signal and macd_histogram > prev_histogram:
            buy_signals += 4
        elif macd < macd_signal and macd_histogram < prev_histogram:
            sell_signals += 4
        
        # Bollinger Bands прорывы (вес 3)
        bb_position = indicators.get('bb_position', 0.5)
        if bb_position < 0.05:
            buy_signals += 3
        elif bb_position > 0.95:
            sell_signals += 3
        
        # Трендовое направление (вес 3)
        current_price = indicators.get('current_price', 0)
        ema_12 = indicators.get('ema_12', 0)
        ema_26 = indicators.get('ema_26', 0)
        
        if current_price > ema_12 > ema_26:
            buy_signals += 3
        elif current_price < ema_12 < ema_26:
            sell_signals += 3
        
        # Новостной сентимент (вес 2)
        if news_sentiment > 0.6:
            buy_signals += 2
        elif news_sentiment < -0.6:
            sell_signals += 2
        
        # Социальный сентимент (вес 1)
        if social_sentiment > 0.6:
            buy_signals += 1
        elif social_sentiment < -0.6:
            sell_signals += 1
        
        # Требуем очень сильное преимущество для ядерной торговли
        if buy_signals >= sell_signals + 6:
            return 'buy'
        elif sell_signals >= buy_signals + 6:
            return 'sell'
        else:
            return 'hold'
    
    def _calculate_nuclear_levels(self, price: float, signal_direction: str, nuclear_analysis: Dict) -> Dict:
        """Расчет ядерных уровней входа и выхода"""
        
        # Адаптивные уровни на основе ядерного потенциала
        score_multiplier = 0.9 + (nuclear_analysis['confidence'] * 0.3)  # 0.9-1.2
        momentum_multiplier = 0.95 + (nuclear_analysis['momentum'] / 100.0 * 0.25)  # 0.95-1.2
        
        # Базовые уровни для ядерной торговли
        base_stop_loss_pct = 0.02  # 2% стоп-лосс (тайтовый из-за высокого плеча)
        
        # Корректируем стоп-лосс
        stop_loss_pct = base_stop_loss_pct * score_multiplier
        
        # Ядерные тейк-профиты
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
    
    def _calculate_nuclear_position_parameters(self, nuclear_analysis: Dict, levels: Dict) -> Dict:
        """Расчет параметров ядерной позиции"""
        
        # Размер позиции на основе ядерного счета
        nuclear_score = nuclear_analysis['nuclear_score']
        confidence = nuclear_analysis['confidence']
        momentum = nuclear_analysis['momentum'] / 100.0
        
        # Выбираем размер позиции на основе ядерного счета
        if nuclear_score >= 99 and confidence > 0.98:
            position_size = self.position_sizes[2]  # Максимальный размер
            leverage = self.leverage_levels[2]      # Максимальное плечо
        elif nuclear_score >= 97 and confidence > 0.96:
            position_size = self.position_sizes[1]  # Средний размер
            leverage = self.leverage_levels[1]      # Среднее плечо
        else:
            position_size = self.position_sizes[0]  # Минимальный размер
            leverage = self.leverage_levels[0]      # Минимальное плечо
        
        # Корректируем на основе соотношения риск/прибыль
        rr_ratio = levels['risk_reward_ratio']
        if rr_ratio > 20.0:  # Исключительное соотношение
            position_size *= 1.1
            leverage *= 1.05
        elif rr_ratio > 15.0:
            position_size *= 1.05
        
        # Ограничения безопасности (даже для ядерного режима)
        position_size = min(position_size, 0.99)  # Максимум 99% капитала
        leverage = min(leverage, 100.0)           # Максимум 100x плечо
        
        return {
            'position_size': position_size,
            'leverage': leverage,
            'effective_exposure': position_size * leverage  # Реальная экспозиция
        }
    
    def _calculate_nuclear_hold_time(self, nuclear_analysis: Dict, market_regime: str) -> int:
        """Расчет времени удержания ядерной позиции (в минутах)"""
        
        base_minutes = {
            NuclearMode.FUSION: 120,       # 2 часа
            NuclearMode.FISSION: 60,       # 1 час
            NuclearMode.ANTIMATTER: 30     # 30 минут
        }
        
        base_time = base_minutes[self.nuclear_mode]
        
        # Корректируем на основе ядерного счета
        score_multiplier = 0.5 + (nuclear_analysis['nuclear_score'] / 100.0)  # 0.5-1.5
        
        # Корректируем на основе рыночного режима
        regime_multiplier = {
            'nuclear_breakout': 2.0,
            'extreme_volatility': 0.5,
            'news_explosion': 0.3,
            'flash_crash': 0.2
        }.get(market_regime, 1.0)
        
        max_minutes = int(base_time * score_multiplier * regime_multiplier)
        return max(15, min(240, max_minutes))  # От 15 минут до 4 часов
    
    def get_nuclear_stats(self) -> Dict:
        """Получение статистики ядерного режима"""
        return {
            'nuclear_mode': self.nuclear_mode.value,
            'target_monthly_return': self._get_target_monthly_return(),
            'min_nuclear_score': self.min_nuclear_score,
            'min_risk_reward_ratio': self.min_risk_reward_ratio,
            'position_sizes': self.position_sizes,
            'leverage_levels': self.leverage_levels,
            'profit_targets': self.profit_targets,
            'volatility_threshold': self.volatility_threshold,
            'confidence_threshold': self.confidence_threshold,
            'expected_win_rate': self._get_expected_win_rate(),
            'max_drawdown_risk': self._get_max_drawdown_risk(),
            'warning': "☢️ КРИТИЧЕСКИ ВЫСОКИЙ РИСК ПОЛНОЙ ПОТЕРИ КАПИТАЛА!"
        }
    
    def _get_target_monthly_return(self) -> float:
        """Целевая месячная доходность"""
        targets = {
            NuclearMode.FUSION: 2.00,      # 200% в месяц
            NuclearMode.FISSION: 5.00,     # 500% в месяц
            NuclearMode.ANTIMATTER: 10.00  # 1000% в месяц
        }
        return targets[self.nuclear_mode]
    
    def _get_expected_win_rate(self) -> float:
        """Ожидаемый винрейт для ядерного режима"""
        rates = {
            NuclearMode.FUSION: 0.25,      # 25%
            NuclearMode.FISSION: 0.20,     # 20%
            NuclearMode.ANTIMATTER: 0.15   # 15%
        }
        return rates[self.nuclear_mode]
    
    def _get_max_drawdown_risk(self) -> float:
        """Максимальный риск просадки"""
        risks = {
            NuclearMode.FUSION: 0.80,      # 80%
            NuclearMode.FISSION: 0.90,     # 90%
            NuclearMode.ANTIMATTER: 0.95   # 95%
        }
        return risks[self.nuclear_mode]

# Глобальные экземпляры для разных ядерных режимов
fusion_engine = NuclearTradingEngine(NuclearMode.FUSION)
fission_engine = NuclearTradingEngine(NuclearMode.FISSION)
antimatter_engine = NuclearTradingEngine(NuclearMode.ANTIMATTER) 