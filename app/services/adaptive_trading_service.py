"""
Адаптивный торговый сервис
Интегрирует Deep Learning Engine с торговой логикой
Реализует профили агрессивности и AI-режимы согласно productContext.md
"""

import logging
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from enum import Enum
import asyncio

from .deep_learning_engine import DeepLearningEngine
from .exchange_service import BingXExchangeService
from .risk_management_service import RiskManagementService
from .market_data_service import MarketDataService, DataSource

logger = logging.getLogger(__name__)

class AggressivenessProfile(Enum):
    """Профили агрессивности торговли"""
    CONSERVATIVE = "conservative"  # 1% риск, широкие стопы, высокие пороги
    MODERATE = "moderate"          # 2% риск, умеренные параметры  
    AGGRESSIVE = "aggressive"      # 5% риск, узкие стопы, низкие пороги

class AIMode(Enum):
    """AI-режимы торговли"""
    MANUAL = "manual"              # только ручные сигналы
    SEMI_AUTO = "semi_auto"        # подтверждение сигналов
    FULL_AUTO = "full_auto"        # автоматическая торговля
    AI_ADAPTIVE = "ai_adaptive"    # полная автономность с ML

class TradingSignal:
    """Торговый сигнал с метаданными"""
    def __init__(self, symbol: str, signal: str, confidence: float, 
                 source: str, timestamp: datetime, metadata: Dict = None):
        self.symbol = symbol
        self.signal = signal  # 'buy', 'sell', 'hold'
        self.confidence = confidence
        self.source = source  # 'ai', 'technical', 'manual'
        self.timestamp = timestamp
        self.metadata = metadata or {}

class AdaptiveTradingService:
    """
    Адаптивный торговый сервис
    Объединяет AI предсказания с торговой логикой
    """
    
    def __init__(self):
        self.dl_engine = DeepLearningEngine()
        self.market_data_service = MarketDataService(default_source=DataSource.DEMO)
        self.exchange_service = None  # Будет инициализирован при необходимости
        self.risk_service = None      # Будет инициализирован при необходимости
        
        # Текущие настройки
        self.current_profile = AggressivenessProfile.MODERATE
        self.current_ai_mode = AIMode.SEMI_AUTO
        
        # Профили агрессивности
        self.profiles = {
            AggressivenessProfile.CONSERVATIVE: {
                'risk_per_trade': 0.01,        # 1% риск
                'stop_loss_atr': 3.0,          # Широкие стопы
                'take_profit_ratio': 3.0,      # Консервативные цели
                'confidence_threshold': 0.8,    # Высокие пороги
                'max_positions': 3,
                'pause_between_trades': 3600,   # 1 час
                'position_size_multiplier': 0.5
            },
            AggressivenessProfile.MODERATE: {
                'risk_per_trade': 0.02,        # 2% риск
                'stop_loss_atr': 2.0,          # Умеренные стопы
                'take_profit_ratio': 2.0,      # Умеренные цели
                'confidence_threshold': 0.65,   # Умеренные пороги
                'max_positions': 5,
                'pause_between_trades': 1800,   # 30 минут
                'position_size_multiplier': 1.0
            },
            AggressivenessProfile.AGGRESSIVE: {
                'risk_per_trade': 0.05,        # 5% риск
                'stop_loss_atr': 1.5,          # Узкие стопы
                'take_profit_ratio': 1.5,      # Агрессивные цели
                'confidence_threshold': 0.55,   # Низкие пороги
                'max_positions': 8,
                'pause_between_trades': 900,    # 15 минут
                'position_size_multiplier': 1.5
            }
        }
        
        # История сигналов и сделок
        self.signal_history: List[TradingSignal] = []
        self.last_trade_time = {}  # symbol -> timestamp
        
        logger.info("Адаптивный торговый сервис инициализирован")
    
    async def initialize(self):
        """Инициализация сервиса"""
        try:
            # Инициализируем Deep Learning Engine
            await self.dl_engine.initialize_models()
            
            # TODO: Инициализировать exchange_service и risk_service
            # self.exchange_service = BingXExchangeService()
            # self.risk_service = RiskManagementService()
            
            logger.info("Адаптивный торговый сервис готов к работе")
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации адаптивного торгового сервиса: {e}")
            return False
    
    def set_aggressiveness_profile(self, profile: AggressivenessProfile):
        """Установка профиля агрессивности"""
        self.current_profile = profile
        logger.info(f"Установлен профиль агрессивности: {profile.value}")
        
        # Обновляем веса моделей в зависимости от профиля
        if profile == AggressivenessProfile.CONSERVATIVE:
            # Консервативный - больше полагаемся на LSTM (долгосрочные тренды)
            self.dl_engine.update_model_weights({'lstm': 0.8, 'cnn': 0.2})
        elif profile == AggressivenessProfile.AGGRESSIVE:
            # Агрессивный - больше полагаемся на CNN (краткосрочные паттерны)
            self.dl_engine.update_model_weights({'lstm': 0.4, 'cnn': 0.6})
        else:
            # Умеренный - сбалансированные веса
            self.dl_engine.update_model_weights({'lstm': 0.6, 'cnn': 0.4})
    
    def set_ai_mode(self, mode: AIMode):
        """Установка AI-режима"""
        self.current_ai_mode = mode
        logger.info(f"Установлен AI-режим: {mode.value}")
    
    async def analyze_market(self, symbol: str, timeframe: str = "1h", periods: int = 100) -> TradingSignal:
        """
        Анализ рынка и генерация торгового сигнала
        """
        try:
            # Получаем реальные рыночные данные
            data = await self.market_data_service.get_ohlcv_data(
                symbol=symbol.replace('/', ''),  # Убираем слэш для API
                timeframe=timeframe,
                limit=periods
            )
            
            # Получаем AI предсказание
            prediction = await self.dl_engine.get_prediction(data, symbol)
            
            if 'error' in prediction:
                logger.error(f"Ошибка получения предсказания: {prediction['error']}")
                return TradingSignal(
                    symbol=symbol,
                    signal='hold',
                    confidence=0.0,
                    source='error',
                    timestamp=datetime.now(),
                    metadata={'error': prediction['error']}
                )
            
            # Извлекаем информацию о сигнале
            combined = prediction.get('combined', {})
            ai_signal = combined.get('signal', 'hold')
            ai_confidence = combined.get('confidence', 0.0)
            
            # Применяем профиль агрессивности
            profile_config = self.profiles[self.current_profile]
            confidence_threshold = profile_config['confidence_threshold']
            
            # Адаптивная корректировка сигнала
            final_signal = self._adapt_signal(ai_signal, ai_confidence, confidence_threshold)
            
            # Создаем торговый сигнал
            trading_signal = TradingSignal(
                symbol=symbol,
                signal=final_signal,
                confidence=ai_confidence,
                source='ai',
                timestamp=datetime.now(),
                metadata={
                    'profile': self.current_profile.value,
                    'ai_mode': self.current_ai_mode.value,
                    'threshold': confidence_threshold,
                    'models': prediction.get('models', {}),
                    'recommendation': combined.get('recommendation', '')
                }
            )
            
            # Сохраняем в историю
            self.signal_history.append(trading_signal)
            
            # Ограничиваем историю последними 1000 сигналами
            if len(self.signal_history) > 1000:
                self.signal_history = self.signal_history[-1000:]
            
            logger.info(f"Сгенерирован сигнал для {symbol}: {final_signal} (уверенность: {ai_confidence:.3f})")
            
            return trading_signal
            
        except Exception as e:
            logger.error(f"Ошибка анализа рынка для {symbol}: {e}")
            return TradingSignal(
                symbol=symbol,
                signal='hold',
                confidence=0.0,
                source='error',
                timestamp=datetime.now(),
                metadata={'error': str(e)}
            )
    
    def _adapt_signal(self, ai_signal: str, confidence: float, threshold: float) -> str:
        """
        Адаптация AI сигнала на основе профиля агрессивности
        """
        # Если уверенность ниже порога - hold
        if confidence < threshold:
            return 'hold'
        
        # Для консервативного профиля - дополнительные проверки
        if self.current_profile == AggressivenessProfile.CONSERVATIVE:
            # Требуем очень высокую уверенность для торговых сигналов
            if ai_signal in ['buy', 'sell'] and confidence < 0.85:
                return 'hold'
        
        # Для агрессивного профиля - снижаем требования
        elif self.current_profile == AggressivenessProfile.AGGRESSIVE:
            # Принимаем сигналы с более низкой уверенностью
            if ai_signal in ['buy', 'sell'] and confidence >= 0.55:
                return ai_signal
        
        return ai_signal
    
    async def should_execute_trade(self, signal: TradingSignal) -> Tuple[bool, str]:
        """
        Проверка, следует ли выполнить торговлю на основе сигнала
        """
        # Проверяем AI-режим
        if self.current_ai_mode == AIMode.MANUAL:
            return False, "Ручной режим - автоматическая торговля отключена"
        
        # Проверяем качество сигнала
        if signal.signal == 'hold':
            return False, "Сигнал: удержание позиции"
        
        # Проверяем паузу между сделками
        profile_config = self.profiles[self.current_profile]
        pause_seconds = profile_config['pause_between_trades']
        
        if signal.symbol in self.last_trade_time:
            time_since_last = (datetime.now() - self.last_trade_time[signal.symbol]).total_seconds()
            if time_since_last < pause_seconds:
                remaining = pause_seconds - time_since_last
                return False, f"Пауза между сделками: осталось {remaining:.0f} секунд"
        
        # Проверяем максимальное количество позиций
        # TODO: Реализовать проверку через exchange_service
        # current_positions = await self.exchange_service.get_open_positions_count()
        # max_positions = profile_config['max_positions']
        # if current_positions >= max_positions:
        #     return False, f"Достигнуто максимальное количество позиций: {max_positions}"
        
        # Для полуавтоматического режима требуется подтверждение
        if self.current_ai_mode == AIMode.SEMI_AUTO:
            return False, "Полуавтоматический режим - требуется подтверждение"
        
        return True, "Сигнал готов к исполнению"
    
    async def calculate_position_size(self, signal: TradingSignal, account_balance: float, 
                                    current_price: float) -> float:
        """
        Расчет размера позиции на основе профиля агрессивности и уверенности AI
        """
        profile_config = self.profiles[self.current_profile]
        base_risk = profile_config['risk_per_trade']
        multiplier = profile_config['position_size_multiplier']
        
        # Адаптивный размер на основе уверенности AI
        confidence_multiplier = signal.confidence  # 0.0 - 1.0
        
        # Итоговый риск
        adjusted_risk = base_risk * multiplier * confidence_multiplier
        
        # Размер позиции в USDT
        position_size = account_balance * adjusted_risk
        
        # Размер позиции в базовой валюте
        position_quantity = position_size / current_price
        
        logger.info(f"Расчет позиции для {signal.symbol}: "
                   f"риск={adjusted_risk:.3f}, размер={position_size:.2f} USDT, "
                   f"количество={position_quantity:.6f}")
        
        return position_quantity
    
    def get_current_settings(self) -> Dict:
        """Получение текущих настроек сервиса"""
        profile_config = self.profiles[self.current_profile]
        
        return {
            'profile': self.current_profile.value,
            'ai_mode': self.current_ai_mode.value,
            'settings': profile_config,
            'model_weights': self.dl_engine.model_weights,
            'signals_count': len(self.signal_history),
            'last_signal': self.signal_history[-1].__dict__ if self.signal_history else None
        }
    
    def get_performance_metrics(self) -> Dict:
        """Получение метрик производительности"""
        if not self.signal_history:
            return {'total_signals': 0}
        
        # Анализ сигналов за последние 24 часа
        recent_signals = [
            s for s in self.signal_history 
            if (datetime.now() - s.timestamp).total_seconds() < 86400
        ]
        
        buy_signals = len([s for s in recent_signals if s.signal == 'buy'])
        sell_signals = len([s for s in recent_signals if s.signal == 'sell'])
        hold_signals = len([s for s in recent_signals if s.signal == 'hold'])
        
        avg_confidence = sum(s.confidence for s in recent_signals) / len(recent_signals) if recent_signals else 0
        
        return {
            'total_signals': len(self.signal_history),
            'recent_signals_24h': len(recent_signals),
            'buy_signals_24h': buy_signals,
            'sell_signals_24h': sell_signals,
            'hold_signals_24h': hold_signals,
            'avg_confidence_24h': round(avg_confidence, 3),
            'current_profile': self.current_profile.value,
            'current_ai_mode': self.current_ai_mode.value
        }
    
    async def _get_market_data(self, symbol: str, timeframe: str, periods: int):
        """
        Заглушка для получения рыночных данных
        TODO: Заменить на реальный вызов к MarketDataService
        """
        import pandas as pd
        import numpy as np
        
        # Генерируем синтетические данные
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='H')
        
        base_price = 50000
        price_changes = np.random.normal(0, 0.02, periods)
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        prices = np.array(prices)
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, periods))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, periods))),
            'close': prices,
            'volume': np.random.uniform(100, 1000, periods)
        })
        
        data['high'] = np.maximum(data['high'], np.maximum(data['open'], data['close']))
        data['low'] = np.minimum(data['low'], np.minimum(data['open'], data['close']))
        
        return data 