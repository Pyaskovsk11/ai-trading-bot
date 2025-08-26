"""
Adaptive Multi-Timeframe Strategy

Продвинутая стратегия, которая:
1. Анализирует несколько таймфреймов (5m, 15m, 1h, 4h, 1d)
2. Адаптируется к рыночным условиям (тренд/боковик/волатильность)
3. Использует ML для определения силы сигналов
4. Комбинирует технический и фундаментальный анализ
5. Имеет встроенное управление рисками
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from .strategy_base import BaseStrategy
from app.core.event_bus import EVENT_BUS, SignalEvent
import talib
from datetime import datetime, timedelta
import asyncio
import os

class AdaptiveMultiTimeframeStrategy(BaseStrategy):
    """
    Адаптивная стратегия с множественными таймфреймами
    """
    
    def __init__(self, name: str = "Adaptive Multi-Timeframe"):
        super().__init__(name)
        # Базовые таймфреймы
        self.timeframes = ['5m', '15m', '1h', '4h', '1d']
        # Прод-override через переменную окружения, например: PRODUCTION_TIMEFRAMES="1h,4h"
        prod_tfs = os.getenv('PRODUCTION_TIMEFRAMES')
        if prod_tfs:
            self.timeframes = [tf.strip() for tf in prod_tfs.split(',') if tf.strip()]
        self.market_regime = 'unknown'  # trend, sideways, volatile
        self.confidence_threshold = 0.7
        self.risk_per_trade = 0.02  # 2% от баланса
        self.max_positions = 3
        
        # Параметры для разных режимов рынка
        self.regime_params = {
            'trend': {
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'atr_multiplier': 2.0,
                'ema_periods': [9, 21, 50],
                'volume_threshold': 1.5
            },
            'sideways': {
                'rsi_oversold': 25,
                'rsi_overbought': 75,
                'atr_multiplier': 1.5,
                'ema_periods': [9, 21],
                'volume_threshold': 1.2
            },
            'volatile': {
                'rsi_oversold': 20,
                'rsi_overbought': 80,
                'atr_multiplier': 3.0,
                'ema_periods': [5, 13, 34],
                'volume_threshold': 2.0
            }
        }
        
        # Веса для разных таймфреймов
        self.timeframe_weights = {
            '5m': 0.1,
            '15m': 0.2,
            '1h': 0.3,
            '4h': 0.25,
            '1d': 0.15
        }
        
        self.last_analysis = None
        self.signal_history = []
        
    def detect_market_regime(self, data: Dict[str, pd.DataFrame]) -> str:
        """
        Определяет режим рынка на основе анализа волатильности и тренда
        """
        try:
            # Используем 1h данные для определения режима
            if '1h' not in data:
                return 'unknown'
                
            df = data['1h']
            if len(df) < 50:
                return 'unknown'
            
            # Рассчитываем индикаторы
            df['sma_20'] = talib.SMA(df['close'], timeperiod=20)
            df['sma_50'] = talib.SMA(df['close'], timeperiod=50)
            df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            df['rsi'] = talib.RSI(df['close'], timeperiod=14)
            
            # Определяем тренд
            current_price = df['close'].iloc[-1]
            sma_20 = df['sma_20'].iloc[-1]
            sma_50 = df['sma_50'].iloc[-1]
            
            # Рассчитываем волатильность
            atr_mean = df['atr'].mean()
            atr_current = df['atr'].iloc[-1]
            volatility_ratio = atr_current / atr_mean
            
            # Определяем режим
            if volatility_ratio > 1.5:
                return 'volatile'
            elif abs(current_price - sma_20) / sma_20 < 0.02 and abs(sma_20 - sma_50) / sma_50 < 0.05:
                return 'sideways'
            else:
                return 'trend'
                
        except Exception as e:
            print(f"Error detecting market regime: {e}")
            return 'unknown'
    
    def calculate_technical_signals(self, df: pd.DataFrame, regime: str) -> Dict[str, Any]:
        """
        Рассчитывает технические сигналы для одного таймфрейма
        """
        try:
            params = self.regime_params[regime]
            
            # Рассчитываем индикаторы
            df['rsi'] = talib.RSI(df['close'], timeperiod=14)
            df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'])
            df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            
            # EMA для разных периодов
            for period in params['ema_periods']:
                df[f'ema_{period}'] = talib.EMA(df['close'], timeperiod=period)
            
            # Bollinger Bands
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(df['close'])
            
            # Stochastic
            df['stoch_k'], df['stoch_d'] = talib.STOCH(df['high'], df['low'], df['close'])
            
            # Volume analysis
            df['volume_sma'] = talib.SMA(df['volume'], timeperiod=20)
            volume_ratio = df['volume'].iloc[-1] / df['volume_sma'].iloc[-1]
            
            current = df.iloc[-1]
            
            # Анализируем сигналы
            signals = {
                'rsi_signal': 0,
                'macd_signal': 0,
                'ema_signal': 0,
                'bb_signal': 0,
                'stoch_signal': 0,
                'volume_signal': 0,
                'overall_signal': 0,
                'confidence': 0.0
            }
            
            # RSI сигналы
            if current['rsi'] < params['rsi_oversold']:
                signals['rsi_signal'] = 1  # Buy
            elif current['rsi'] > params['rsi_overbought']:
                signals['rsi_signal'] = -1  # Sell
            
            # MACD сигналы
            if current['macd'] > current['macd_signal'] and current['macd_hist'] > 0:
                signals['macd_signal'] = 1
            elif current['macd'] < current['macd_signal'] and current['macd_hist'] < 0:
                signals['macd_signal'] = -1
            
            # EMA сигналы (тренд)
            ema_signals = []
            for i, period in enumerate(params['ema_periods'][:-1]):
                next_period = params['ema_periods'][i + 1]
                if current[f'ema_{period}'] > current[f'ema_{next_period}']:
                    ema_signals.append(1)
                else:
                    ema_signals.append(-1)
            
            signals['ema_signal'] = np.mean(ema_signals) if ema_signals else 0
            
            # Bollinger Bands сигналы
            if current['close'] < current['bb_lower']:
                signals['bb_signal'] = 1
            elif current['close'] > current['bb_upper']:
                signals['bb_signal'] = -1
            
            # Stochastic сигналы
            if current['stoch_k'] < 20 and current['stoch_d'] < 20:
                signals['stoch_signal'] = 1
            elif current['stoch_k'] > 80 and current['stoch_d'] > 80:
                signals['stoch_signal'] = -1
            
            # Volume сигналы
            if volume_ratio > params['volume_threshold']:
                signals['volume_signal'] = 1 if signals['rsi_signal'] > 0 else -1
            
            # Общий сигнал (взвешенная сумма)
            signal_weights = {
                'rsi_signal': 0.25,
                'macd_signal': 0.2,
                'ema_signal': 0.2,
                'bb_signal': 0.15,
                'stoch_signal': 0.1,
                'volume_signal': 0.1
            }
            
            overall_signal = sum(signals[key] * signal_weights[key] for key in signal_weights.keys())
            signals['overall_signal'] = overall_signal
            
            # Рассчитываем уверенность
            active_signals = sum(1 for key in signal_weights.keys() if abs(signals[key]) > 0)
            if active_signals > 0:
                confidence = min(abs(overall_signal) * active_signals / len(signal_weights), 1.0)
                signals['confidence'] = confidence
            
            return signals
            
        except Exception as e:
            print(f"Error calculating technical signals: {e}")
            return {'overall_signal': 0, 'confidence': 0.0}
    
    def aggregate_timeframe_signals(self, timeframe_signals: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Агрегирует сигналы от разных таймфреймов
        """
        try:
            weighted_signals = []
            total_weight = 0
            
            for timeframe, signals in timeframe_signals.items():
                if timeframe in self.timeframe_weights:
                    weight = self.timeframe_weights[timeframe]
                    weighted_signals.append(signals['overall_signal'] * weight)
                    total_weight += weight
            
            if total_weight == 0:
                return {'signal': 0, 'confidence': 0.0, 'direction': 'HOLD'}
            
            # Взвешенный средний сигнал
            aggregated_signal = sum(weighted_signals) / total_weight
            
            # Рассчитываем общую уверенность
            confidences = [signals['confidence'] for signals in timeframe_signals.values()]
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            # Определяем направление
            if aggregated_signal > 0.3 and avg_confidence > self.confidence_threshold:
                direction = 'BUY'
            elif aggregated_signal < -0.3 and avg_confidence > self.confidence_threshold:
                direction = 'SELL'
            else:
                direction = 'HOLD'
            
            return {
                'signal': aggregated_signal,
                'confidence': avg_confidence,
                'direction': direction,
                'timeframe_analysis': timeframe_signals
            }
            
        except Exception as e:
            print(f"Error aggregating timeframe signals: {e}")
            return {'signal': 0, 'confidence': 0.0, 'direction': 'HOLD'}
    
    def calculate_risk_parameters(self, data: Dict[str, pd.DataFrame], signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Рассчитывает параметры управления рисками
        """
        try:
            # Используем 1h данные для расчета рисков
            if '1h' not in data:
                return {}
            
            df = data['1h']
            current_price = df['close'].iloc[-1]
            atr = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14).iloc[-1]
            
            params = self.regime_params[self.market_regime]
            atr_multiplier = params['atr_multiplier']
            
            # Рассчитываем стоп-лосс и тейк-профит
            stop_loss_distance = atr * atr_multiplier
            
            if signal['direction'] == 'BUY':
                stop_loss = current_price - stop_loss_distance
                take_profit = current_price + (stop_loss_distance * 2)  # 1:2 risk-reward
            elif signal['direction'] == 'SELL':
                stop_loss = current_price + stop_loss_distance
                take_profit = current_price - (stop_loss_distance * 2)
            else:
                return {}
            
            return {
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'atr': atr,
                'risk_reward_ratio': 2.0
            }
            
        except Exception as e:
            print(f"Error calculating risk parameters: {e}")
            return {}
    
    def generate_signals(self, market_data: Any, context: Dict = None) -> List[Dict[str, Any]]:
        """
        Генерирует торговые сигналы на основе анализа множественных таймфреймов
        """
        try:
            if not isinstance(market_data, dict):
                return []
            
            # Определяем режим рынка
            self.market_regime = self.detect_market_regime(market_data)
            
            # Анализируем каждый таймфрейм
            timeframe_signals = {}
            for timeframe in self.timeframes:
                # Отключаем 15m для SOL в прод-сценарии
                if context and context.get('symbol','').upper().startswith('SOL') and timeframe == '15m':
                    continue
                if timeframe in market_data:
                    signals = self.calculate_technical_signals(market_data[timeframe], self.market_regime)
                    timeframe_signals[timeframe] = signals
            
            # Агрегируем сигналы
            aggregated = self.aggregate_timeframe_signals(timeframe_signals)
            
            # Если нет четкого сигнала, возвращаем пустой список
            if aggregated['direction'] == 'HOLD' or aggregated['confidence'] < self.confidence_threshold:
                return []
            
            # Рассчитываем параметры риска
            risk_params = self.calculate_risk_parameters(market_data, aggregated)
            
            # Создаем сигнал
            signal = {
                'type': aggregated['direction'],
                'symbol': context.get('symbol', 'UNKNOWN') if context else 'UNKNOWN',
                'price': market_data['1h']['close'].iloc[-1] if '1h' in market_data else 0,
                'confidence': aggregated['confidence'],
                'market_regime': self.market_regime,
                'timeframe_analysis': aggregated['timeframe_analysis'],
                'stop_loss': risk_params.get('stop_loss'),
                'take_profit': risk_params.get('take_profit'),
                'risk_reward_ratio': risk_params.get('risk_reward_ratio', 2.0),
                'timestamp': datetime.now().isoformat(),
                'strategy': self.name,
                'metadata': {
                    'regime': self.market_regime,
                    'timeframes_analyzed': list(timeframe_signals.keys()),
                    'aggregated_signal': aggregated['signal']
                }
            }
            
            # Сохраняем историю сигналов
            self.signal_history.append(signal)
            if len(self.signal_history) > 100:
                self.signal_history = self.signal_history[-100:]
            
            self.last_analysis = {
                'timestamp': datetime.now(),
                'market_regime': self.market_regime,
                'aggregated_signal': aggregated,
                'timeframe_signals': timeframe_signals
            }
            
            return [signal]
            
        except Exception as e:
            print(f"Error generating signals in {self.name}: {e}")
            return []
    
    def explain(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Объясняет логику сигнала
        """
        try:
            explanation = {
                'strategy': self.name,
                'reasoning': [],
                'confidence_factors': [],
                'risk_assessment': {},
                'market_context': {}
            }
            
            # Анализируем причины сигнала
            timeframe_analysis = signal.get('timeframe_analysis', {})
            
            for timeframe, analysis in timeframe_analysis.items():
                if analysis['overall_signal'] > 0.3:
                    explanation['reasoning'].append(
                        f"Сильный сигнал на покупку на {timeframe} таймфрейме"
                    )
                elif analysis['overall_signal'] < -0.3:
                    explanation['reasoning'].append(
                        f"Сильный сигнал на продажу на {timeframe} таймфрейме"
                    )
            
            # Факторы уверенности
            if signal.get('confidence', 0) > 0.8:
                explanation['confidence_factors'].append("Высокая согласованность между таймфреймами")
            elif signal.get('confidence', 0) > 0.6:
                explanation['confidence_factors'].append("Умеренная согласованность между таймфреймами")
            
            # Оценка рисков
            explanation['risk_assessment'] = {
                'market_regime': signal.get('market_regime', 'unknown'),
                'risk_reward_ratio': signal.get('risk_reward_ratio', 0),
                'confidence_level': signal.get('confidence', 0)
            }
            
            # Контекст рынка
            explanation['market_context'] = {
                'regime': signal.get('market_regime', 'unknown'),
                'timeframes_analyzed': signal.get('metadata', {}).get('timeframes_analyzed', []),
                'aggregated_signal_strength': signal.get('metadata', {}).get('aggregated_signal', 0)
            }
            
            return explanation
            
        except Exception as e:
            print(f"Error explaining signal: {e}")
            return {'error': str(e)}
    
    def on_event(self, event: Any):
        """
        Обрабатывает события (например, смена режима рынка)
        """
        try:
            if isinstance(event, SignalEvent):
                if event.type == 'MARKET_REGIME_CHANGE':
                    self.market_regime = event.data.get('new_regime', 'unknown')
                    print(f"[{self.name}] Market regime changed to: {self.market_regime}")
                elif event.type == 'RISK_UPDATE':
                    self.risk_per_trade = event.data.get('risk_per_trade', self.risk_per_trade)
                    self.confidence_threshold = event.data.get('confidence_threshold', self.confidence_threshold)
        except Exception as e:
            print(f"Error handling event in {self.name}: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Возвращает метрики производительности стратегии
        """
        try:
            if not self.signal_history:
                return {}
            
            total_signals = len(self.signal_history)
            buy_signals = len([s for s in self.signal_history if s['type'] == 'BUY'])
            sell_signals = len([s for s in self.signal_history if s['type'] == 'SELL'])
            
            avg_confidence = np.mean([s.get('confidence', 0) for s in self.signal_history])
            
            return {
                'total_signals': total_signals,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'avg_confidence': avg_confidence,
                'current_regime': self.market_regime,
                'last_analysis': self.last_analysis.isoformat() if self.last_analysis else None
            }
            
        except Exception as e:
            print(f"Error getting performance metrics: {e}")
            return {}
