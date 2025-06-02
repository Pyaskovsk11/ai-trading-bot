#!/usr/bin/env python3
"""
ScalpingEngine - Специализированный движок для скальпинговых стратегий
Оптимизирован для работы на коротких таймфреймах (1m, 5m, 15m)
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio

from .bingx_historical_data_service import bingx_historical_service
from .backtest_engine import BacktestEngine, BacktestConfig, BacktestTrade

logger = logging.getLogger(__name__)

class ScalpingStrategy(Enum):
    """Типы скальпинговых стратегий"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    VOLUME_SPIKE = "volume_spike"
    MICRO_TREND = "micro_trend"

@dataclass
class ScalpingConfig:
    """Конфигурация скальпинга"""
    timeframe: str = "5m"  # 1m, 5m, 15m
    max_trade_duration_minutes: int = 30  # Максимальная длительность сделки
    min_profit_target: float = 0.002  # 0.2% минимальная цель прибыли
    max_loss_limit: float = 0.001  # 0.1% максимальный убыток
    position_size_pct: float = 0.05  # 5% от капитала на сделку
    max_concurrent_trades: int = 3  # Максимум одновременных сделок
    signal_threshold: int = 3  # Минимальный порог сигнала (ЭКСТРЕМАЛЬНО НИЗКИЙ)
    use_trailing_stop: bool = True
    trailing_stop_pct: float = 0.0005  # 0.05% трейлинг стоп

class ScalpingEngine(BacktestEngine):
    """
    Специализированный движок для скальпинговых стратегий
    Наследует от BacktestEngine и добавляет скальпинговую логику
    """
    
    def __init__(self, scalping_config: ScalpingConfig, backtest_config: BacktestConfig = None):
        super().__init__(backtest_config)
        self.scalping_config = scalping_config
        self.micro_signals_cache = {}  # Кэш микро-сигналов
        self.price_action_buffer = {}  # Буфер ценового действия
        
        logger.info(f"ScalpingEngine инициализирован для таймфрейма {scalping_config.timeframe}")
    
    async def run_scalping_backtest(self, 
                                  symbols: List[str],
                                  start_date: datetime,
                                  end_date: datetime) -> Dict[str, Any]:
        """Запуск скальпингового бэктеста"""
        logger.info(f"🚀 Запуск скальпингового бэктеста на {self.scalping_config.timeframe}")
        
        try:
            # Получаем данные с высокой частотой
            historical_data = await self._get_high_frequency_data(symbols, start_date, end_date)
            
            # Запускаем скальпинговый цикл
            await self._run_scalping_loop(historical_data, symbols)
            
            # Закрываем все позиции
            await self._close_all_positions(end_date)
            
            # Рассчитываем метрики
            metrics = await self._calculate_metrics()
            
            result = {
                'scalping_config': self.scalping_config.__dict__,
                'backtest_config': self.config.__dict__,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'timeframe': self.scalping_config.timeframe
                },
                'symbols': symbols,
                'metrics': metrics.__dict__,
                'trades': [trade.__dict__ for trade in self.trades],
                'equity_curve': self.equity_curve,
                'scalping_summary': self._generate_scalping_summary(metrics)
            }
            
            logger.info(f"✅ Скальпинговый бэктест завершен: {metrics.total_trades} сделок")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка скальпингового бэктеста: {e}")
            raise
    
    async def _get_high_frequency_data(self, 
                                     symbols: List[str], 
                                     start_date: datetime, 
                                     end_date: datetime) -> Dict[str, pd.DataFrame]:
        """Получение высокочастотных данных"""
        logger.info(f"📊 Получение данных {self.scalping_config.timeframe} для скальпинга")
        
        try:
            historical_data = await bingx_historical_service.get_multiple_symbols_data(
                symbols, start_date, end_date, self.scalping_config.timeframe
            )
            
            for symbol, data in historical_data.items():
                if len(data) > 0:
                    logger.info(f"✅ {symbol}: {len(data)} свечей {self.scalping_config.timeframe}")
                    # Добавляем технические индикаторы для скальпинга
                    historical_data[symbol] = self._add_scalping_indicators(data)
                
            return historical_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения высокочастотных данных: {e}")
            # Fallback на синтетические данные
            return await self._generate_synthetic_scalping_data(symbols, start_date, end_date)
    
    def _add_scalping_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Добавление индикаторов для скальпинга"""
        # Быстрые EMA для скальпинга
        df['ema_3'] = df['close'].ewm(span=3).mean()
        df['ema_8'] = df['close'].ewm(span=8).mean()
        df['ema_21'] = df['close'].ewm(span=21).mean()
        
        # Быстрый RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
        rs = gain / loss
        df['rsi_fast'] = 100 - (100 / (1 + rs))
        
        # Быстрый MACD
        ema_5 = df['close'].ewm(span=5).mean()
        ema_13 = df['close'].ewm(span=13).mean()
        df['macd_fast'] = ema_5 - ema_13
        df['macd_signal_fast'] = df['macd_fast'].ewm(span=3).mean()
        
        # Bollinger Bands для скальпинга
        bb_period = 10
        df['bb_middle'] = df['close'].rolling(bb_period).mean()
        bb_std = df['close'].rolling(bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 1.5)  # Более узкие полосы
        df['bb_lower'] = df['bb_middle'] - (bb_std * 1.5)
        
        # Ценовое действие
        df['price_change'] = df['close'].pct_change()
        df['volume_change'] = df['volume'].pct_change()
        df['volatility'] = df['price_change'].rolling(10).std()
        
        # Уровни поддержки/сопротивления
        df['resistance'] = df['high'].rolling(20).max()
        df['support'] = df['low'].rolling(20).min()
        
        return df
    
    async def _run_scalping_loop(self, 
                               historical_data: Dict[str, pd.DataFrame], 
                               symbols: List[str]):
        """Основной цикл скальпинга"""
        # Получаем все временные метки
        all_timestamps = set()
        for data in historical_data.values():
            all_timestamps.update(data.index)
        
        timestamps = sorted(all_timestamps)
        
        for i, timestamp in enumerate(timestamps):
            # Обновляем текущие цены
            current_prices = {}
            current_data = {}
            
            for symbol in symbols:
                if timestamp in historical_data[symbol].index:
                    row = historical_data[symbol].loc[timestamp]
                    current_prices[symbol] = row['close']
                    current_data[symbol] = row
            
            # Обновляем портфель
            await self._update_portfolio_value(current_prices, timestamp)
            
            # Проверяем условия выхода (более частые проверки для скальпинга)
            await self._check_scalping_exit_conditions(current_prices, current_data, timestamp)
            
            # Генерируем скальпинговые сигналы КАЖДЫЙ тик
            await self._process_scalping_signals(symbols, current_prices, current_data, timestamp)
            
            # Записываем состояние портфеля чаще
            if i % 5 == 0:  # Каждые 5 тиков
                self._record_equity_point(timestamp, current_prices)
    
    async def _process_scalping_signals(self, 
                                      symbols: List[str], 
                                      current_prices: Dict[str, float], 
                                      current_data: Dict[str, Any], 
                                      timestamp: datetime):
        """Обработка скальпинговых сигналов"""
        for symbol in symbols:
            if symbol not in current_prices or symbol not in current_data:
                continue
            
            # Проверяем лимит одновременных сделок
            if len(self.open_positions) >= self.scalping_config.max_concurrent_trades:
                continue
                
            # Проверяем, нет ли уже позиции по этому символу
            if symbol in self.open_positions:
                continue
            
            try:
                # Генерируем скальпинговый сигнал
                signal = await self._generate_scalping_signal(symbol, current_prices[symbol], current_data[symbol], timestamp)
                
                # Выполняем вход если сигнал достаточно сильный
                if signal and signal.get('should_execute', False):
                    await self._execute_scalping_entry(symbol, signal, current_prices[symbol], timestamp)
                    
            except Exception as e:
                logger.error(f"Ошибка обработки скальпингового сигнала для {symbol}: {e}")
    
    async def _generate_scalping_signal(self, 
                                      symbol: str, 
                                      price: float, 
                                      data: Any, 
                                      timestamp: datetime) -> Dict:
        """Генерация скальпингового сигнала с ЭКСТРЕМАЛЬНО низкими порогами"""
        try:
            signal_score = 0
            signal_factors = []
            signal_type = 'hold'
            
            # Быстрые EMA сигналы (высокий вес для скальпинга)
            if hasattr(data, 'ema_3') and hasattr(data, 'ema_8'):
                if data.ema_3 > data.ema_8:
                    signal_score += 3  # Сильный вес для быстрых EMA
                    signal_factors.append("EMA3 > EMA8 (бычий)")
                elif data.ema_3 < data.ema_8:
                    signal_score -= 3
                    signal_factors.append("EMA3 < EMA8 (медвежий)")
            
            # Быстрый RSI
            if hasattr(data, 'rsi_fast'):
                if data.rsi_fast < 35:  # Более агрессивные уровни для скальпинга
                    signal_score += 2
                    signal_factors.append(f"RSI_fast низкий ({data.rsi_fast:.1f})")
                elif data.rsi_fast > 65:
                    signal_score -= 2
                    signal_factors.append(f"RSI_fast высокий ({data.rsi_fast:.1f})")
            
            # Быстрый MACD
            if hasattr(data, 'macd_fast') and hasattr(data, 'macd_signal_fast'):
                if data.macd_fast > data.macd_signal_fast:
                    signal_score += 2
                    signal_factors.append("MACD_fast бычий")
                elif data.macd_fast < data.macd_signal_fast:
                    signal_score -= 2
                    signal_factors.append("MACD_fast медвежий")
            
            # Bollinger Bands для скальпинга
            if hasattr(data, 'bb_upper') and hasattr(data, 'bb_lower'):
                bb_position = (price - data.bb_lower) / (data.bb_upper - data.bb_lower)
                if bb_position < 0.2:  # Близко к нижней границе
                    signal_score += 2
                    signal_factors.append("Цена у нижней BB")
                elif bb_position > 0.8:  # Близко к верхней границе
                    signal_score -= 2
                    signal_factors.append("Цена у верхней BB")
            
            # Ценовое действие
            if hasattr(data, 'price_change'):
                if abs(data.price_change) > 0.001:  # 0.1% движение
                    if data.price_change > 0:
                        signal_score += 1
                        signal_factors.append(f"Рост цены ({data.price_change*100:.2f}%)")
                    else:
                        signal_score -= 1
                        signal_factors.append(f"Падение цены ({data.price_change*100:.2f}%)")
            
            # Объемные всплески
            if hasattr(data, 'volume_change'):
                if data.volume_change > 0.5:  # 50% рост объема
                    signal_score += 1
                    signal_factors.append("Всплеск объема")
            
            # ЭКСТРЕМАЛЬНО НИЗКИЕ ПОРОГИ для скальпинга
            if signal_score >= 3:  # ОЧЕНЬ низкий порог
                signal_type = 'buy'
                confidence = min(0.8, abs(signal_score) / 10.0)
                stop_loss = price * 0.999  # 0.1% стоп-лосс
                take_profit = price * 1.003  # 0.3% тейк-профит
                
            elif signal_score <= -3:
                signal_type = 'sell'
                confidence = min(0.8, abs(signal_score) / 10.0)
                stop_loss = price * 1.001  # 0.1% стоп-лосс
                take_profit = price * 0.997  # 0.3% тейк-профит
                
            else:
                return {'signal': 'hold', 'should_execute': False, 'reason': 'Недостаточно сигнала для скальпинга'}
            
            return {
                'signal': signal_type,
                'should_execute': True,
                'confidence': confidence,
                'strategy_type': 'scalping',
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reason': f"Скальпинг {signal_type.upper()} (score: {signal_score}): " + "; ".join(signal_factors[:3]),
                'signal_score': signal_score,
                'factors': signal_factors
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации скальпингового сигнала: {e}")
            return {'signal': 'hold', 'should_execute': False, 'reason': f'Ошибка: {str(e)}'}
    
    async def _execute_scalping_entry(self, 
                                    symbol: str, 
                                    signal: Dict, 
                                    price: float, 
                                    timestamp: datetime):
        """Выполнение входа в скальпинговую позицию"""
        # Рассчитываем размер позиции для скальпинга
        position_value = self.current_capital * self.scalping_config.position_size_pct
        position_size = position_value / price
        
        # Применяем комиссию и проскальзывание
        entry_price = self._apply_slippage(price, signal.get('signal', 'buy'))
        commission = position_size * entry_price * self.config.commission_rate
        
        # Проверяем достаточность капитала
        required_capital = position_size * entry_price + commission
        if required_capital > self.current_capital:
            return
        
        # Обеспечиваем, что timestamp - это datetime объект
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
        elif isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.now()
        
        # Создаем скальпинговую сделку
        self.trade_counter += 1
        trade = BacktestTrade(
            id=self.trade_counter,
            symbol=symbol,
            side=signal.get('signal', 'buy'),
            entry_time=timestamp,
            entry_price=entry_price,
            quantity=position_size,
            commission=commission,
            strategy_type='scalping',
            confidence=signal.get('confidence', 0.5),
            stop_loss=signal.get('stop_loss'),
            take_profit=signal.get('take_profit')
        )
        
        # Обновляем капитал
        self.current_capital -= required_capital
        
        # Добавляем в открытые позиции
        self.open_positions[symbol] = trade
        
        logger.debug(f"🎯 Скальпинговый вход: {symbol} {signal.get('signal', 'buy')} @ ${entry_price:.4f}")
    
    async def _check_scalping_exit_conditions(self, 
                                            current_prices: Dict[str, float], 
                                            current_data: Dict[str, Any], 
                                            timestamp: datetime):
        """Проверка условий выхода для скальпинга"""
        positions_to_close = []
        
        for symbol, trade in self.open_positions.items():
            if symbol not in current_prices:
                continue
                
            current_price = current_prices[symbol]
            
            # Проверяем стоп-лосс и тейк-профит
            if trade.stop_loss and self._check_stop_loss(trade, current_price):
                positions_to_close.append((symbol, current_price, "stop_loss"))
                continue
                
            if trade.take_profit and self._check_take_profit(trade, current_price):
                positions_to_close.append((symbol, current_price, "take_profit"))
                continue
            
            # Проверяем максимальное время для скальпинга
            try:
                # Обеспечиваем, что timestamp - это datetime объект
                if isinstance(timestamp, (int, float)):
                    timestamp = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
                elif isinstance(timestamp, pd.Timestamp):
                    timestamp = timestamp.to_pydatetime()
                elif not isinstance(timestamp, datetime):
                    timestamp = datetime.now()
                
                duration_minutes = (timestamp - trade.entry_time).total_seconds() / 60
                if duration_minutes >= self.scalping_config.max_trade_duration_minutes:
                    positions_to_close.append((symbol, current_price, "time_limit_scalping"))
                    continue
            except (AttributeError, TypeError):
                # Если не можем рассчитать время, пропускаем проверку времени
                pass
            
            # Трейлинг стоп для скальпинга
            if self.scalping_config.use_trailing_stop:
                if self._check_trailing_stop(trade, current_price):
                    positions_to_close.append((symbol, current_price, "trailing_stop"))
        
        # Закрываем позиции
        for symbol, exit_price, reason in positions_to_close:
            await self._execute_exit(symbol, exit_price, timestamp, reason)
    
    def _check_trailing_stop(self, trade: BacktestTrade, current_price: float) -> bool:
        """Проверка трейлинг стопа"""
        if trade.side == 'buy':
            # Для покупки: если цена упала на trailing_stop_pct от максимума
            max_price = getattr(trade, 'max_price', trade.entry_price)
            if current_price > max_price:
                trade.max_price = current_price
                return False
            return (max_price - current_price) / max_price >= self.scalping_config.trailing_stop_pct
        else:
            # Для продажи: если цена выросла на trailing_stop_pct от минимума
            min_price = getattr(trade, 'min_price', trade.entry_price)
            if current_price < min_price:
                trade.min_price = current_price
                return False
            return (current_price - min_price) / min_price >= self.scalping_config.trailing_stop_pct
    
    async def _generate_synthetic_scalping_data(self, 
                                              symbols: List[str], 
                                              start_date: datetime, 
                                              end_date: datetime) -> Dict[str, pd.DataFrame]:
        """Генерация синтетических данных для скальпинга"""
        freq_map = {'1m': '1T', '5m': '5T', '15m': '15T'}
        freq = freq_map.get(self.scalping_config.timeframe, '5T')
        
        historical_data = {}
        for symbol in symbols:
            dates = pd.date_range(start=start_date, end=end_date, freq=freq)
            
            # Генерируем более волатильные данные для скальпинга
            base_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 1.0
            
            # Высокочастотные колебания
            np.random.seed(hash(symbol) % 2**32)
            returns = np.random.normal(0, 0.005, len(dates))  # 0.5% волатильность
            
            # Добавляем микро-тренды
            micro_trends = np.sin(np.arange(len(dates)) * 0.1) * 0.002
            
            prices = base_price * np.exp(np.cumsum(returns + micro_trends))
            
            df = pd.DataFrame({
                'timestamp': dates,
                'open': prices,
                'high': prices * (1 + np.abs(np.random.normal(0, 0.002, len(dates)))),
                'low': prices * (1 - np.abs(np.random.normal(0, 0.002, len(dates)))),
                'close': prices,
                'volume': np.random.uniform(100000, 1000000, len(dates))
            })
            
            df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
            df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))
            
            # Добавляем скальпинговые индикаторы
            df = self._add_scalping_indicators(df)
            
            historical_data[symbol] = df
            
        return historical_data
    
    def _generate_scalping_summary(self, metrics) -> Dict[str, str]:
        """Генерация сводки скальпинговых результатов"""
        avg_trade_duration_minutes = metrics.avg_trade_duration if hasattr(metrics, 'avg_trade_duration') else 0
        
        return {
            'strategy': f"Скальпинг на {self.scalping_config.timeframe}",
            'performance': f"Доходность: {metrics.total_return_pct:.3f}% (${metrics.total_return:,.2f})",
            'trading': f"Сделок: {metrics.total_trades}, Винрейт: {metrics.win_rate:.1%}",
            'timing': f"Средняя длительность: {avg_trade_duration_minutes:.1f} мин",
            'risk': f"Макс. просадка: {metrics.max_drawdown_pct:.3f}%"
        }

# Глобальный экземпляр
scalping_engine = None

def create_scalping_engine(timeframe: str = "5m") -> ScalpingEngine:
    """Создание экземпляра скальпингового движка"""
    scalping_config = ScalpingConfig(timeframe=timeframe)
    backtest_config = BacktestConfig(
        initial_capital=50000.0,
        commission_rate=0.001,
        slippage_rate=0.0002,  # Меньше проскальзывание для скальпинга
        position_sizing_method="fixed_pct"
    )
    
    return ScalpingEngine(scalping_config, backtest_config) 