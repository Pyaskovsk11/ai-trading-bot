"""
Unified Trading Strategy Manager
Объединяет все торговые стратегии в единую систему
"""

import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from enum import Enum
import asyncio

from .adaptive_trading_service import AdaptiveTradingService, AggressivenessProfile, AIMode, TradingSignal
from .deep_learning_engine import DeepLearningEngine
from .signal_generation_service import generate_signal_for_asset
from .risk_management_service import RiskManagementService

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    """Типы торговых стратегий"""
    ADAPTIVE = "adaptive"           # Адаптивная стратегия (РЕКОМЕНДУЕТСЯ)
    ML_ONLY = "ml_only"            # Только Deep Learning
    BASIC = "basic"                # Базовая генерация сигналов
    ENSEMBLE = "ensemble"          # Комбинированная стратегия
    CUSTOM = "custom"              # Пользовательская стратегия

class StrategyConfig:
    """Конфигурация стратегии"""
    def __init__(self, 
                 strategy_type: StrategyType = StrategyType.ADAPTIVE,
                 aggressiveness: AggressivenessProfile = AggressivenessProfile.MODERATE,
                 ai_mode: AIMode = AIMode.SEMI_AUTO,
                 ensemble_weights: Dict[str, float] = None):
        self.strategy_type = strategy_type
        self.aggressiveness = aggressiveness
        self.ai_mode = ai_mode
        self.ensemble_weights = ensemble_weights or {
            'adaptive': 0.5,
            'ml': 0.3,
            'basic': 0.2
        }

class UnifiedTradingSignal:
    """Унифицированный торговый сигнал"""
    def __init__(self, 
                 symbol: str,
                 signal: str,
                 confidence: float,
                 strategy_type: str,
                 timestamp: datetime,
                 metadata: Dict = None,
                 risk_metrics: Dict = None):
        self.symbol = symbol
        self.signal = signal  # 'buy', 'sell', 'hold'
        self.confidence = confidence
        self.strategy_type = strategy_type
        self.timestamp = timestamp
        self.metadata = metadata or {}
        self.risk_metrics = risk_metrics or {}
        
        # Рекомендации по исполнению
        self.should_execute = False
        self.position_size = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        self.execution_reason = ""

class TradingStrategyManager:
    """
    Унифицированный менеджер торговых стратегий
    Объединяет все подходы в единую систему
    """
    
    def __init__(self):
        # Инициализация всех стратегий
        self.adaptive_strategy = AdaptiveTradingService()
        self.ml_engine = DeepLearningEngine()
        self.risk_manager = RiskManagementService()
        
        # Текущая конфигурация
        self.current_config = StrategyConfig()
        self.current_aggressiveness = AggressivenessProfile.MODERATE
        
        # История сигналов
        self.signal_history: List[UnifiedTradingSignal] = []
        
        # Статистика производительности
        self.performance_stats = {
            'total_signals': 0,
            'successful_signals': 0,
            'failed_signals': 0,
            'strategy_performance': {}
        }
        
        logger.info("TradingStrategyManager инициализирован")
    
    async def initialize(self):
        """Инициализация всех компонентов"""
        try:
            # Инициализируем адаптивную стратегию
            await self.adaptive_strategy.initialize()
            
            # Инициализируем ML engine
            await self.ml_engine.initialize_models()
            
            logger.info("TradingStrategyManager готов к работе")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации TradingStrategyManager: {e}")
            return False
    
    def set_strategy_config(self, config: StrategyConfig):
        """Установка конфигурации стратегии"""
        self.current_config = config
        self.current_aggressiveness = config.aggressiveness
        
        # Применяем настройки к адаптивной стратегии
        if hasattr(self.adaptive_strategy, 'set_aggressiveness_profile'):
            self.adaptive_strategy.set_aggressiveness_profile(config.aggressiveness)
        
        if hasattr(self.adaptive_strategy, 'set_ai_mode'):
            self.adaptive_strategy.set_ai_mode(config.ai_mode)
        
        logger.info(f"Установлена конфигурация: {config.strategy_type.value}, "
                   f"агрессивность: {config.aggressiveness.value}, "
                   f"AI режим: {config.ai_mode.value}")
    
    async def get_unified_signal(self, symbol: str, timeframe: str = "1h") -> UnifiedTradingSignal:
        """
        Получение унифицированного торгового сигнала
        """
        try:
            strategy_type = self.current_config.strategy_type
            
            if strategy_type == StrategyType.ADAPTIVE:
                return await self._get_adaptive_signal(symbol, timeframe)
            elif strategy_type == StrategyType.ML_ONLY:
                return await self._get_ml_signal(symbol, timeframe)
            elif strategy_type == StrategyType.BASIC:
                return await self._get_basic_signal(symbol)
            elif strategy_type == StrategyType.ENSEMBLE:
                return await self._get_ensemble_signal(symbol, timeframe)
            else:
                raise ValueError(f"Неподдерживаемый тип стратегии: {strategy_type}")
                
        except Exception as e:
            logger.error(f"Ошибка получения сигнала для {symbol}: {e}")
            return self._create_error_signal(symbol, str(e))
    
    async def _get_adaptive_signal(self, symbol: str, timeframe: str) -> UnifiedTradingSignal:
        """Получение сигнала от адаптивной стратегии"""
        try:
            # Получаем сигнал от адаптивной стратегии
            adaptive_signal = await self.adaptive_strategy.analyze_market(symbol, timeframe)
            
            # Конвертируем в унифицированный формат
            unified_signal = UnifiedTradingSignal(
                symbol=symbol,
                signal=adaptive_signal.signal,
                confidence=adaptive_signal.confidence,
                strategy_type="adaptive",
                timestamp=adaptive_signal.timestamp,
                metadata={
                    'profile': self.current_config.aggressiveness.value,
                    'ai_mode': self.current_config.ai_mode.value,
                    'source_metadata': adaptive_signal.metadata
                }
            )
            
            # Применяем риск-менеджмент
            await self._apply_risk_management(unified_signal)
            
            return unified_signal
            
        except Exception as e:
            logger.error(f"Ошибка адаптивной стратегии для {symbol}: {e}")
            return self._create_error_signal(symbol, str(e))
    
    async def _get_ml_signal(self, symbol: str, timeframe: str) -> UnifiedTradingSignal:
        """Получение сигнала от ML engine"""
        try:
            # Получаем данные для ML анализа
            data = await self._get_market_data(symbol, timeframe)
            
            # Получаем предсказание от ML
            ml_prediction = await self.ml_engine.get_prediction(data, symbol)
            
            if 'error' in ml_prediction:
                return self._create_error_signal(symbol, ml_prediction['error'])
            
            combined = ml_prediction.get('combined', {})
            
            unified_signal = UnifiedTradingSignal(
                symbol=symbol,
                signal=combined.get('signal', 'hold'),
                confidence=combined.get('confidence', 0.0),
                strategy_type="ml_only",
                timestamp=datetime.now(),
                metadata={
                    'models': ml_prediction.get('models', {}),
                    'recommendation': combined.get('recommendation', ''),
                    'model_weights': self.ml_engine.model_weights
                }
            )
            
            await self._apply_risk_management(unified_signal)
            return unified_signal
            
        except Exception as e:
            logger.error(f"Ошибка ML стратегии для {symbol}: {e}")
            return self._create_error_signal(symbol, str(e))
    
    async def _get_basic_signal(self, symbol: str) -> UnifiedTradingSignal:
        """Получение сигнала от базовой стратегии"""
        try:
            # Заглушка для базовой стратегии (требует DB session)
            # В реальной реализации здесь будет вызов generate_signal_for_asset
            
            unified_signal = UnifiedTradingSignal(
                symbol=symbol,
                signal='hold',
                confidence=0.5,
                strategy_type="basic",
                timestamp=datetime.now(),
                metadata={
                    'note': 'Basic strategy temporarily disabled - requires DB connection',
                    'fallback': True
                }
            )
            
            await self._apply_risk_management(unified_signal)
            return unified_signal
            
        except Exception as e:
            logger.error(f"Ошибка базовой стратегии для {symbol}: {e}")
            return self._create_error_signal(symbol, str(e))
    
    async def _get_ensemble_signal(self, symbol: str, timeframe: str) -> UnifiedTradingSignal:
        """Получение комбинированного сигнала от всех стратегий"""
        try:
            # Получаем сигналы от всех стратегий
            adaptive_signal = await self._get_adaptive_signal(symbol, timeframe)
            ml_signal = await self._get_ml_signal(symbol, timeframe)
            basic_signal = await self._get_basic_signal(symbol)
            
            # Веса для комбинирования
            weights = self.current_config.ensemble_weights
            
            # Комбинируем сигналы
            combined_signal = self._combine_signals([
                (adaptive_signal, weights.get('adaptive', 0.5)),
                (ml_signal, weights.get('ml', 0.3)),
                (basic_signal, weights.get('basic', 0.2))
            ])
            
            combined_signal.strategy_type = "ensemble"
            combined_signal.metadata['ensemble_weights'] = weights
            combined_signal.metadata['component_signals'] = {
                'adaptive': {
                    'signal': adaptive_signal.signal,
                    'confidence': adaptive_signal.confidence
                },
                'ml': {
                    'signal': ml_signal.signal,
                    'confidence': ml_signal.confidence
                },
                'basic': {
                    'signal': basic_signal.signal,
                    'confidence': basic_signal.confidence
                }
            }
            
            await self._apply_risk_management(combined_signal)
            return combined_signal
            
        except Exception as e:
            logger.error(f"Ошибка ensemble стратегии для {symbol}: {e}")
            return self._create_error_signal(symbol, str(e))
    
    def _combine_signals(self, weighted_signals: List[Tuple[UnifiedTradingSignal, float]]) -> UnifiedTradingSignal:
        """Комбинирование сигналов с весами"""
        if not weighted_signals:
            return self._create_error_signal("UNKNOWN", "No signals to combine")
        
        # Подсчет взвешенных голосов
        buy_weight = 0.0
        sell_weight = 0.0
        hold_weight = 0.0
        total_confidence = 0.0
        total_weight = 0.0
        
        symbol = weighted_signals[0][0].symbol
        
        for signal, weight in weighted_signals:
            if signal.signal == 'buy':
                buy_weight += weight * signal.confidence
            elif signal.signal == 'sell':
                sell_weight += weight * signal.confidence
            else:  # hold
                hold_weight += weight * signal.confidence
            
            total_confidence += signal.confidence * weight
            total_weight += weight
        
        # Определяем финальный сигнал
        if buy_weight > sell_weight and buy_weight > hold_weight:
            final_signal = 'buy'
        elif sell_weight > buy_weight and sell_weight > hold_weight:
            final_signal = 'sell'
        else:
            final_signal = 'hold'
        
        # Нормализуем уверенность
        final_confidence = total_confidence / total_weight if total_weight > 0 else 0.0
        
        return UnifiedTradingSignal(
            symbol=symbol,
            signal=final_signal,
            confidence=final_confidence,
            strategy_type="ensemble",
            timestamp=datetime.now(),
            metadata={
                'weights': {
                    'buy': buy_weight,
                    'sell': sell_weight,
                    'hold': hold_weight
                }
            }
        )
    
    async def _apply_risk_management(self, signal: UnifiedTradingSignal):
        """Применение риск-менеджмента к сигналу"""
        try:
            # Базовые параметры
            balance = 10000.0  # TODO: получать реальный баланс
            current_price = 50000.0  # TODO: получать реальную цену
            
            # Получаем профиль агрессивности
            profile = self.current_config.aggressiveness
            
            # Определяем риск на сделку
            if profile == AggressivenessProfile.CONSERVATIVE:
                risk_per_trade = 0.01
                stop_loss_pct = 0.03
            elif profile == AggressivenessProfile.AGGRESSIVE:
                risk_per_trade = 0.05
                stop_loss_pct = 0.015
            else:  # MODERATE
                risk_per_trade = 0.02
                stop_loss_pct = 0.02
            
            # Корректируем риск на основе уверенности AI
            adjusted_risk = risk_per_trade * signal.confidence
            
            # Применяем риск-менеджмент
            from .risk_management_service import apply_risk_management
            risk_result = apply_risk_management(
                balance, current_price, adjusted_risk, stop_loss_pct
            )
            
            # Заполняем метрики риска
            signal.risk_metrics = {
                'risk_per_trade': risk_per_trade,
                'adjusted_risk': adjusted_risk,
                'stop_loss_pct': stop_loss_pct,
                'position_size': risk_result.get('position_size', 0.0),
                'stop_loss': risk_result.get('stop_loss', current_price)
            }
            
            # Определяем, следует ли выполнить сделку
            if signal.signal in ['buy', 'sell'] and signal.confidence > 0.6:
                signal.should_execute = True
                signal.position_size = risk_result.get('position_size', 0.0)
                signal.stop_loss = risk_result.get('stop_loss', current_price)
                signal.execution_reason = f"Сигнал {signal.signal} с уверенностью {signal.confidence:.2f}"
            else:
                signal.should_execute = False
                signal.execution_reason = f"Низкая уверенность ({signal.confidence:.2f}) или сигнал hold"
            
        except Exception as e:
            logger.error(f"Ошибка применения риск-менеджмента: {e}")
            signal.risk_metrics = {'error': str(e)}
    
    def _create_error_signal(self, symbol: str, error_message: str) -> UnifiedTradingSignal:
        """Создание сигнала об ошибке"""
        return UnifiedTradingSignal(
            symbol=symbol,
            signal='hold',
            confidence=0.0,
            strategy_type="error",
            timestamp=datetime.now(),
            metadata={'error': error_message}
        )
    
    async def _get_market_data(self, symbol: str, timeframe: str):
        """Получение рыночных данных (заглушка)"""
        # TODO: Интегрировать с реальным источником данных
        import pandas as pd
        import numpy as np
        
        # Генерируем синтетические данные для тестирования
        periods = 100
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='h')
        
        base_price = 50000
        price_changes = np.random.normal(0, 0.02, periods)
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        prices = np.array(prices)
        
        # Создаем данные с правильным количеством признаков (6)
        data = pd.DataFrame({
            'open': prices,
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, periods))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, periods))),
            'close': prices,
            'volume': np.random.uniform(100, 1000, periods),
            'timestamp': dates
        })
        
        data['high'] = np.maximum(data['high'], np.maximum(data['open'], data['close']))
        data['low'] = np.minimum(data['low'], np.minimum(data['open'], data['close']))
        
        return data
    
    def add_signal_to_history(self, signal: UnifiedTradingSignal):
        """Добавление сигнала в историю"""
        self.signal_history.append(signal)
        
        # Ограничиваем историю последними 1000 сигналами
        if len(self.signal_history) > 1000:
            self.signal_history = self.signal_history[-1000:]
        
        # Обновляем статистику
        self.performance_stats['total_signals'] += 1
    
    def get_performance_metrics(self) -> Dict:
        """Получение метрик производительности"""
        if not self.signal_history:
            return {
                'total_signals': 0,
                'recent_signals_24h': 0,
                'buy_signals_24h': 0,
                'sell_signals_24h': 0,
                'hold_signals_24h': 0,
                'avg_confidence_24h': 0.0,
                'current_strategy': self.current_config.strategy_type.value,
                'current_profile': self.current_config.aggressiveness.value,
                'current_ai_mode': self.current_config.ai_mode.value,
                'strategy_performance': {}
            }
        
        # Анализ сигналов за последние 24 часа
        recent_signals = [
            s for s in self.signal_history 
            if (datetime.now() - s.timestamp).total_seconds() < 86400
        ]
        
        buy_signals = len([s for s in recent_signals if s.signal == 'buy'])
        sell_signals = len([s for s in recent_signals if s.signal == 'sell'])
        hold_signals = len([s for s in recent_signals if s.signal == 'hold'])
        
        avg_confidence = sum(s.confidence for s in recent_signals) / len(recent_signals) if recent_signals else 0
        
        # Статистика по стратегиям
        strategy_stats = {}
        for strategy_type in ['adaptive', 'ml_only', 'basic', 'ensemble']:
            strategy_signals = [s for s in recent_signals if s.strategy_type == strategy_type]
            strategy_stats[strategy_type] = {
                'count': len(strategy_signals),
                'avg_confidence': sum(s.confidence for s in strategy_signals) / len(strategy_signals) if strategy_signals else 0
            }
        
        return {
            'total_signals': len(self.signal_history),
            'recent_signals_24h': len(recent_signals),
            'buy_signals_24h': buy_signals,
            'sell_signals_24h': sell_signals,
            'hold_signals_24h': hold_signals,
            'avg_confidence_24h': round(avg_confidence, 3),
            'current_strategy': self.current_config.strategy_type.value,
            'current_profile': self.current_config.aggressiveness.value,
            'current_ai_mode': self.current_config.ai_mode.value,
            'strategy_performance': strategy_stats
        }
    
    def get_current_config(self) -> Dict:
        """Получение текущей конфигурации"""
        return {
            'strategy_type': self.current_config.strategy_type.value,
            'aggressiveness': self.current_config.aggressiveness.value,
            'ai_mode': self.current_config.ai_mode.value,
            'ensemble_weights': self.current_config.ensemble_weights
        }

# Глобальный экземпляр менеджера стратегий
strategy_manager = TradingStrategyManager() 