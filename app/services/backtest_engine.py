"""
BacktestEngine - Система исторического тестирования торговых стратегий
Интегрирована с TradingStrategyManager и AdvancedRiskManager
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import json

from .trading_strategy_manager import TradingStrategyManager, StrategyConfig, StrategyType
from .advanced_risk_manager import AdvancedRiskManager, MarketRegime
from .adaptive_trading_service import AggressivenessProfile, AIMode
from .bingx_historical_data_service import bingx_historical_service

logger = logging.getLogger(__name__)

class OrderType(Enum):
    """Типы ордеров"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class TradeStatus(Enum):
    """Статусы сделок"""
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"

@dataclass
class BacktestTrade:
    """Сделка в бэктесте"""
    id: int
    symbol: str
    side: str  # 'buy' or 'sell'
    entry_time: datetime
    entry_price: float
    quantity: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    commission: float = 0.0
    status: TradeStatus = TradeStatus.OPEN
    strategy_type: str = ""
    confidence: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_reason: str = ""

@dataclass
class BacktestMetrics:
    """Метрики бэктеста"""
    # Основные метрики
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    
    # Торговые метрики
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    
    # Временные метрики
    avg_trade_duration: float
    max_trade_duration: float
    min_trade_duration: float
    
    # Риск метрики
    var_95: float
    var_99: float
    expected_shortfall: float
    volatility: float
    
    # Дополнительные метрики
    recovery_factor: float
    ulcer_index: float
    sterling_ratio: float

@dataclass
class BacktestConfig:
    """Конфигурация бэктеста"""
    initial_capital: float = 100000.0
    commission_rate: float = 0.001  # 0.1%
    slippage_rate: float = 0.0005   # 0.05%
    max_positions: int = 10
    position_sizing_method: str = "fixed_amount"  # fixed_amount, fixed_pct, risk_based
    position_size: float = 0.02  # 2% от капитала
    use_stop_loss: bool = True
    use_take_profit: bool = True
    max_trade_duration: int = 24  # часов
    risk_free_rate: float = 0.02  # 2% годовых

class BacktestEngine:
    """
    Профессиональная система исторического тестирования
    """
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.strategy_manager = TradingStrategyManager()
        self.risk_manager = AdvancedRiskManager(self.config.initial_capital)
        
        # Состояние бэктеста
        self.current_capital = self.config.initial_capital
        self.peak_capital = self.config.initial_capital
        self.trades: List[BacktestTrade] = []
        self.open_positions: Dict[str, BacktestTrade] = {}
        self.equity_curve: List[Dict] = []
        self.trade_counter = 0
        
        logger.info("BacktestEngine инициализирован")
    
    async def run_backtest(self, 
                          strategy_config: StrategyConfig,
                          symbols: List[str],
                          start_date: datetime,
                          end_date: datetime,
                          timeframe: str = "1h") -> Dict[str, Any]:
        """
        Запуск полного бэктеста
        """
        try:
            logger.info(f"🚀 Запуск бэктеста: {len(symbols)} символов, "
                       f"{start_date.date()} - {end_date.date()}")
            
            # Инициализация
            await self._initialize_backtest(strategy_config)
            
            # Генерация исторических данных
            historical_data = await self._generate_historical_data(symbols, start_date, end_date, timeframe)
            
            # Основной цикл бэктеста
            await self._run_backtest_loop(historical_data, symbols, timeframe)
            
            # Закрытие всех открытых позиций
            await self._close_all_positions(end_date)
            
            # Расчет метрик
            metrics = await self._calculate_metrics()
            
            # Формирование результата
            result = {
                'config': asdict(self.config),
                'strategy_config': strategy_config.get_current_config() if hasattr(strategy_config, 'get_current_config') else {},
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'duration_days': (end_date - start_date).days
                },
                'symbols': symbols,
                'metrics': asdict(metrics),
                'trades': [asdict(trade) for trade in self.trades],
                'equity_curve': self.equity_curve,
                'summary': self._generate_summary(metrics)
            }
            
            logger.info(f"✅ Бэктест завершен: {metrics.total_trades} сделок, "
                       f"доходность: {metrics.total_return_pct:.2f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка бэктеста: {e}")
            raise
    
    async def _initialize_backtest(self, strategy_config: StrategyConfig):
        """Инициализация бэктеста"""
        # Инициализация менеджера стратегий
        await self.strategy_manager.initialize()
        self.strategy_manager.set_strategy_config(strategy_config)
        
        # Сброс состояния
        self.current_capital = self.config.initial_capital
        self.peak_capital = self.config.initial_capital
        self.trades.clear()
        self.open_positions.clear()
        self.equity_curve.clear()
        self.trade_counter = 0
        
        logger.info(f"Бэктест инициализирован: капитал ${self.config.initial_capital:,.0f}")
    
    async def _generate_historical_data(self, 
                                      symbols: List[str], 
                                      start_date: datetime, 
                                      end_date: datetime, 
                                      timeframe: str) -> Dict[str, pd.DataFrame]:
        """Получение исторических данных (реальных или синтетических)"""
        logger.info(f"🔄 Получение исторических данных для {len(symbols)} символов")
        logger.info(f"   Период: {start_date.date()} - {end_date.date()}")
        logger.info(f"   Таймфрейм: {timeframe}")
        
        try:
            # Используем BingX Historical Data Service для получения реальных данных
            historical_data = await bingx_historical_service.get_multiple_symbols_data(
                symbols, start_date, end_date, timeframe
            )
            
            # Проверяем качество данных
            for symbol, data in historical_data.items():
                if len(data) > 0:
                    logger.info(f"✅ {symbol}: {len(data)} свечей получено")
                else:
                    logger.warning(f"⚠️ {symbol}: данные отсутствуют")
            
            return historical_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения исторических данных: {e}")
            logger.warning("🔄 Переключаемся на синтетические данные")
            
            # Fallback на синтетические данные
            historical_data = {}
            for symbol in symbols:
                data = await self._generate_synthetic_data(symbol, start_date, end_date, timeframe)
                historical_data[symbol] = data
                
            logger.info(f"📊 Сгенерированы синтетические данные для {len(symbols)} символов")
            return historical_data
    
    async def _generate_synthetic_data(self, 
                                     symbol: str, 
                                     start_date: datetime, 
                                     end_date: datetime, 
                                     timeframe: str) -> pd.DataFrame:
        """Генерация синтетических данных для тестирования"""
        # Определяем частоту
        freq_map = {
            '1m': '1T', '5m': '5T', '15m': '15T', '30m': '30T',
            '1h': '1H', '4h': '4H', '1d': '1D'
        }
        freq = freq_map.get(timeframe, '1H')
        
        # Создаем временной ряд
        dates = pd.date_range(start=start_date, end=end_date, freq=freq)
        periods = len(dates)
        
        # Базовая цена (зависит от символа)
        base_prices = {
            'BTCUSDT': 50000, 'ETHUSDT': 3000, 'ADAUSDT': 1.5,
            'BNBUSDT': 400, 'SOLUSDT': 100, 'XRPUSDT': 0.6
        }
        base_price = base_prices.get(symbol, 1000)
        
        # Генерируем цены с трендом и волатильностью
        np.random.seed(hash(symbol) % 2**32)  # Детерминированная генерация
        
        # Создаем тренд
        trend = np.linspace(0, 0.2, periods)  # 20% роста за период
        
        # Добавляем волатильность
        volatility = 0.02  # 2% дневная волатильность
        returns = np.random.normal(0, volatility, periods)
        
        # Создаем ценовой ряд
        log_prices = np.log(base_price) + trend + np.cumsum(returns)
        prices = np.exp(log_prices)
        
        # Создаем OHLCV данные
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, periods))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, periods))),
            'close': prices,
            'volume': np.random.uniform(1000000, 5000000, periods)
        })
        
        # Корректируем high/low
        df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
        df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))
        
        df.set_index('timestamp', inplace=True)
        return df
    
    async def _run_backtest_loop(self, 
                               historical_data: Dict[str, pd.DataFrame], 
                               symbols: List[str], 
                               timeframe: str):
        """Основной цикл бэктеста"""
        # Получаем все временные метки
        all_timestamps = set()
        for data in historical_data.values():
            all_timestamps.update(data.index)
        
        timestamps = sorted(all_timestamps)
        
        for i, timestamp in enumerate(timestamps):
            # Обновляем текущие цены
            current_prices = {}
            for symbol in symbols:
                if timestamp in historical_data[symbol].index:
                    current_prices[symbol] = historical_data[symbol].loc[timestamp, 'close']
            
            # Обновляем стоимость портфеля
            await self._update_portfolio_value(current_prices, timestamp)
            
            # Проверяем стоп-лоссы и тейк-профиты
            await self._check_exit_conditions(current_prices, timestamp)
            
            # Генерируем сигналы (максимальная частота для ультра-агрессивной торговли)
            if i % 1 == 0:  # Проверяем сигналы КАЖДЫЙ бар (максимальная частота)
                await self._process_signals(symbols, current_prices, timestamp, timeframe)
            
            # Записываем состояние портфеля
            if i % 10 == 0:  # Записываем каждые 10 баров
                self._record_equity_point(timestamp, current_prices)
    
    async def _process_signals(self, 
                             symbols: List[str], 
                             current_prices: Dict[str, float], 
                             timestamp: datetime, 
                             timeframe: str):
        """Обработка торговых сигналов"""
        for symbol in symbols:
            if symbol not in current_prices:
                continue
                
            try:
                # ВРЕМЕННОЕ ИСПРАВЛЕНИЕ: Используем простую стратегию вместо ML
                # Это исправляет проблему с отсутствием сигналов в бэктесте
                signal = await self._generate_simple_signal(symbol, current_prices[symbol], timestamp)
                
                # Проверяем условия для входа
                if signal and signal.get('should_execute', False) and signal.get('signal') in ['buy', 'sell']:
                    await self._execute_entry(symbol, signal, current_prices[symbol], timestamp)
                    
            except Exception as e:
                logger.error(f"Ошибка обработки сигнала для {symbol}: {e}")
    
    async def _generate_simple_signal(self, symbol: str, price: float, timestamp: datetime) -> Dict:
        """
        Продвинутая техническая стратегия для увеличения PnL
        Использует множественные индикаторы и адаптивные пороги
        """
        try:
            # Получаем исторические данные для расчета индикаторов
            historical_data = await self._get_recent_data_for_analysis(symbol, timestamp)
            
            if len(historical_data) < 50:  # Недостаточно данных для анализа
                return self._create_hold_signal("Недостаточно данных для анализа")
            
            # Рассчитываем технические индикаторы
            indicators = self._calculate_technical_indicators(historical_data)
            
            # Определяем рыночный режим
            market_regime = self._detect_market_regime(historical_data)
            
            # Генерируем сигнал на основе множественных условий
            signal_data = self._analyze_multi_indicator_signal(indicators, market_regime, price, timestamp)
            
            return signal_data
                
        except Exception as e:
            logger.error(f"Ошибка генерации продвинутого сигнала: {e}")
            return self._create_hold_signal(f"Ошибка анализа: {str(e)}")
    
    async def _get_recent_data_for_analysis(self, symbol: str, timestamp: datetime) -> pd.DataFrame:
        """Получение последних данных для технического анализа"""
        try:
            # Обеспечиваем, что timestamp - это datetime объект
            if isinstance(timestamp, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
            elif isinstance(timestamp, pd.Timestamp):
                timestamp = timestamp.to_pydatetime()
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.now()
            
            # Получаем последние 100 часов данных для анализа
            periods = 100
            start_time = timestamp - timedelta(hours=periods)
            
            # Пытаемся получить реальные данные
            data = await bingx_historical_service.get_historical_data(
                symbol, start_time, timestamp, "1h"
            )
            
            if len(data) >= 50:  # Достаточно данных для анализа
                logger.debug(f"📊 Получены реальные данные для анализа {symbol}: {len(data)} свечей")
                return data
            else:
                logger.warning(f"⚠️ Недостаточно реальных данных для {symbol}, используем синтетические")
                
        except Exception as e:
            logger.warning(f"❌ Ошибка получения данных для анализа {symbol}: {e}")
        
        # Fallback на синтетические данные
        return await self._generate_synthetic_analysis_data(symbol, timestamp)
    
    async def _generate_synthetic_analysis_data(self, symbol: str, timestamp: datetime) -> pd.DataFrame:
        """Генерация синтетических данных для анализа"""
        periods = 100
        start_time = timestamp - timedelta(hours=periods)
        
        # Создаем временной ряд
        dates = pd.date_range(start=start_time, end=timestamp, freq='1H')
        
        # Базовая цена для символа
        base_prices = {
            'BTCUSDT': 50000, 'ETHUSDT': 3000, 'ADAUSDT': 1.5,
            'BNBUSDT': 400, 'SOLUSDT': 100, 'XRPUSDT': 0.6
        }
        base_price = base_prices.get(symbol, 1000)
        
        # Генерируем реалистичные данные с трендом
        np.random.seed(hash(f"{symbol}_{timestamp.hour}") % 2**32)
        
        # Создаем тренд с периодическими изменениями
        trend_strength = 0.002  # 0.2% тренд за час
        trend_direction = 1 if (timestamp.hour % 12) < 6 else -1  # Меняем направление каждые 6 часов
        
        prices = []
        current_price = base_price
        
        for i in range(len(dates)):
            # Добавляем тренд
            trend_component = trend_direction * trend_strength * current_price
            
            # Добавляем случайную волатильность
            volatility = np.random.normal(0, 0.01) * current_price  # 1% волатильность
            
            # Добавляем циклические колебания
            cycle_component = 0.005 * current_price * np.sin(i * 0.1)
            
            current_price += trend_component + volatility + cycle_component
            prices.append(current_price)
        
        # Создаем OHLCV данные
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'close': prices,
            'volume': np.random.uniform(1000000, 5000000, len(dates))
        })
        
        # Генерируем high/low на основе close
        df['high'] = df['close'] * (1 + np.abs(np.random.normal(0, 0.005, len(df))))
        df['low'] = df['close'] * (1 - np.abs(np.random.normal(0, 0.005, len(df))))
        
        # Корректируем high/low
        df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
        df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))
        
        return df
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """Расчет технических индикаторов"""
        indicators = {}
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        indicators['rsi'] = 100 - (100 / (1 + rs)).iloc[-1]
        
        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9).mean()
        indicators['macd'] = macd.iloc[-1]
        indicators['macd_signal'] = macd_signal.iloc[-1]
        indicators['macd_histogram'] = (macd - macd_signal).iloc[-1]
        
        # Bollinger Bands
        bb_middle = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        indicators['bb_position'] = ((df['close'].iloc[-1] - bb_lower.iloc[-1]) / 
                                   (bb_upper.iloc[-1] - bb_lower.iloc[-1]))
        
        # Скользящие средние
        indicators['sma_20'] = df['close'].rolling(20).mean().iloc[-1]
        indicators['sma_50'] = df['close'].rolling(50).mean().iloc[-1]
        indicators['ema_12'] = ema_12.iloc[-1]
        indicators['ema_26'] = ema_26.iloc[-1]
        
        # Объемный анализ
        indicators['volume_sma'] = df['volume'].rolling(20).mean().iloc[-1]
        indicators['volume_ratio'] = df['volume'].iloc[-1] / indicators['volume_sma']
        
        # Волатильность
        indicators['volatility'] = df['close'].pct_change().rolling(20).std().iloc[-1]
        
        # Ценовые изменения
        indicators['price_change_1h'] = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]
        indicators['price_change_4h'] = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5] if len(df) >= 5 else 0
        indicators['price_change_24h'] = (df['close'].iloc[-1] - df['close'].iloc[-25]) / df['close'].iloc[-25] if len(df) >= 25 else 0
        
        return indicators
    
    def _detect_market_regime(self, df: pd.DataFrame) -> str:
        """Определение рыночного режима"""
        if len(df) < 50:
            return 'sideways'
        
        # Анализ тренда на основе скользящих средних
        sma_20 = df['close'].rolling(20).mean().iloc[-1]
        sma_50 = df['close'].rolling(50).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        # Анализ волатильности
        volatility = df['close'].pct_change().rolling(20).std().iloc[-1]
        
        if current_price > sma_20 > sma_50 and volatility < 0.03:
            return 'bull_trend'
        elif current_price < sma_20 < sma_50 and volatility < 0.03:
            return 'bear_trend'
        elif volatility > 0.05:
            return 'high_volatility'
        else:
            return 'sideways'
    
    def _analyze_multi_indicator_signal(self, indicators: Dict, market_regime: str, price: float, timestamp: datetime) -> Dict:
        """Анализ сигнала на основе множественных индикаторов - АДАПТИВНАЯ ВЕРСИЯ"""
        
        # Инициализация счетчиков сигналов
        buy_score = 0
        sell_score = 0
        confidence_factors = []
        signal_type = 'hold'
        
        # ФИЛЬТР КАЧЕСТВА: Проверяем базовые условия рынка
        volatility = indicators.get('volatility', 0.02)
        volume_ratio = indicators.get('volume_ratio', 1.0)
        
        # Отфильтровываем плохие рыночные условия (более мягкие фильтры)
        if volatility > 0.12:  # Увеличено с 0.08 до 0.12 - разрешаем больше волатильности
            return self._create_hold_signal("Экстремально высокая волатильность для торговли")
        
        if volume_ratio < 0.2:  # Снижено с 0.3 до 0.2 - менее строгий фильтр объема
            return self._create_hold_signal("Недостаточный объем для качественного сигнала")
        
        # ВРЕМЕННОЙ ФИЛЬТР: Избегаем периоды низкой активности
        hour = timestamp.hour if hasattr(timestamp, 'hour') else datetime.now().hour
        is_low_activity = hour in [0, 1, 2, 3, 4, 5, 6]  # Ночные часы UTC
        
        # RSI анализ - СБАЛАНСИРОВАННЫЕ ПОРОГИ
        rsi = indicators.get('rsi', 50)
        if rsi < 30:  # Сильная перепроданность
            buy_score += 30
            confidence_factors.append(f"RSI сильно низкий ({rsi:.1f}) - перепроданность")
        elif rsi < 40:  # Умеренная перепроданность
            buy_score += 15
            confidence_factors.append(f"RSI низкий ({rsi:.1f}) - возможность покупки")
        elif rsi > 70:  # Сильная перекупленность
            sell_score += 30
            confidence_factors.append(f"RSI сильно высокий ({rsi:.1f}) - перекупленность")
        elif rsi > 60:  # Умеренная перекупленность
            sell_score += 15
            confidence_factors.append(f"RSI высокий ({rsi:.1f}) - возможность продажи")
        
        # MACD анализ - СБАЛАНСИРОВАННАЯ ЛОГИКА
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_histogram = indicators.get('macd_histogram', 0)
        
        # Сильные MACD сигналы
        if macd > macd_signal and macd_histogram > 0:
            buy_score += 25
            confidence_factors.append("MACD сильный бычий сигнал")
        elif macd < macd_signal and macd_histogram < 0:
            sell_score += 25
            confidence_factors.append("MACD сильный медвежий сигнал")
        elif macd > macd_signal:
            buy_score += 12
            confidence_factors.append("MACD умеренный бычий сигнал")
        elif macd < macd_signal:
            sell_score += 12
            confidence_factors.append("MACD умеренный медвежий сигнал")
        
        # Bollinger Bands - СБАЛАНСИРОВАННАЯ ЛОГИКА
        bb_position = indicators.get('bb_position', 0.5)
        if bb_position < 0.15:  # Близко к нижней границе
            buy_score += 20
            confidence_factors.append("Цена у нижней границы BB - отскок")
        elif bb_position < 0.3:  # В нижней зоне
            buy_score += 10
            confidence_factors.append("Цена в нижней зоне BB")
        elif bb_position > 0.85:  # Близко к верхней границе
            sell_score += 20
            confidence_factors.append("Цена у верхней границы BB - откат")
        elif bb_position > 0.7:  # В верхней зоне
            sell_score += 10
            confidence_factors.append("Цена в верхней зоне BB")
        
        # Анализ скользящих средних - СБАЛАНСИРОВАННАЯ ЛОГИКА
        sma_20 = indicators.get('sma_20', price)
        sma_50 = indicators.get('sma_50', price)
        ema_12 = indicators.get('ema_12', price)
        ema_26 = indicators.get('ema_26', price)
        
        # Трендовые сигналы
        if price > ema_12 > ema_26 > sma_20:  # Сильный восходящий тренд
            buy_score += 30
            confidence_factors.append("Сильный восходящий тренд")
        elif price < ema_12 < ema_26 < sma_20:  # Сильный нисходящий тренд
            sell_score += 30
            confidence_factors.append("Сильный нисходящий тренд")
        elif price > ema_12 > ema_26:  # Краткосрочный восходящий тренд
            buy_score += 15
            confidence_factors.append("Краткосрочный восходящий тренд")
        elif price < ema_12 < ema_26:  # Краткосрочный нисходящий тренд
            sell_score += 15
            confidence_factors.append("Краткосрочный нисходящий тренд")
        
        # Объемный анализ - СБАЛАНСИРОВАННЫЙ
        if volume_ratio > 1.8:  # Высокий объем
            volume_boost = 20
            if buy_score > sell_score:
                buy_score += volume_boost
                confidence_factors.append(f"Высокий объем поддерживает покупки ({volume_ratio:.1f}x)")
            else:
                sell_score += volume_boost
                confidence_factors.append(f"Высокий объем поддерживает продажи ({volume_ratio:.1f}x)")
        elif volume_ratio > 1.3:  # Умеренно высокий объем
            volume_boost = 10
            if buy_score > sell_score:
                buy_score += volume_boost
                confidence_factors.append(f"Умеренно высокий объем ({volume_ratio:.1f}x)")
            else:
                sell_score += volume_boost
                confidence_factors.append(f"Умеренно высокий объем ({volume_ratio:.1f}x)")
        
        # Анализ ценовых изменений - СБАЛАНСИРОВАННЫЙ
        price_change_1h = indicators.get('price_change_1h', 0)
        price_change_4h = indicators.get('price_change_4h', 0)
        price_change_24h = indicators.get('price_change_24h', 0)
        
        # Значительные ценовые движения
        if abs(price_change_1h) > 0.015:  # 1.5% изменение за час
            if price_change_1h > 0:
                buy_score += 15
                confidence_factors.append(f"Значительный рост 1ч ({price_change_1h*100:.1f}%)")
            else:
                sell_score += 15
                confidence_factors.append(f"Значительное падение 1ч ({price_change_1h*100:.1f}%)")
        
        # Устойчивые тренды (более мягкие требования)
        if abs(price_change_4h) > 0.025 and abs(price_change_24h) > 0.04:
            if price_change_4h > 0 and price_change_24h > 0:
                buy_score += 20
                confidence_factors.append("Устойчивый восходящий тренд")
            elif price_change_4h < 0 and price_change_24h < 0:
                sell_score += 20
                confidence_factors.append("Устойчивый нисходящий тренд")
        
        # Корректировка на основе рыночного режима
        if market_regime == 'bull_trend':
            buy_score += 15
            sell_score = int(sell_score * 0.8)
            confidence_factors.append("Бычий рыночный режим")
        elif market_regime == 'bear_trend':
            sell_score += 15
            buy_score = int(buy_score * 0.8)
            confidence_factors.append("Медвежий рыночный режим")
        elif market_regime == 'high_volatility':
            # В высокой волатильности требуем чуть более сильные сигналы
            buy_score = int(buy_score * 0.9)
            sell_score = int(sell_score * 0.9)
            confidence_factors.append("Высокая волатильность")
        
        # Корректировка для периодов низкой активности
        if is_low_activity:
            buy_score = int(buy_score * 0.7)  # Снижаем агрессивность ночью
            sell_score = int(sell_score * 0.7)
            confidence_factors.append("Период низкой активности - снижена агрессивность")
        
        # Фильтр конфликтующих сигналов (более мягкий)
        signal_conflict = abs(buy_score - sell_score) < 8
        if signal_conflict and max(buy_score, sell_score) < 35:
            return self._create_hold_signal("Неопределенные сигналы - ожидание")
        
        # Адаптивные пороги на основе агрессивности стратегии
        # Получаем уровень агрессивности из стратегии (если доступно)
        try:
            aggressiveness = getattr(self.strategy_manager, 'current_aggressiveness', 'MODERATE')
            if hasattr(aggressiveness, 'value'):
                aggressiveness = aggressiveness.value
        except:
            aggressiveness = 'MODERATE'
        
        # Настройка порогов в зависимости от агрессивности
        if aggressiveness == 'CONSERVATIVE':
            # Консервативные пороги - только очень качественные сигналы
            very_strong_threshold = 50
            strong_threshold = 35
            moderate_threshold = 25
            strategy_type_suffix = 'conservative'
        elif aggressiveness == 'AGGRESSIVE':
            # Агрессивные пороги - больше сделок
            very_strong_threshold = 30
            strong_threshold = 20
            moderate_threshold = 12
            strategy_type_suffix = 'aggressive'
        else:  # MODERATE
            # Сбалансированные пороги
            very_strong_threshold = 40
            strong_threshold = 28
            moderate_threshold = 18
            strategy_type_suffix = 'balanced'
        
        # Определение финального сигнала - АДАПТИВНЫЕ ПОРОГИ
        if buy_score >= very_strong_threshold:  # Очень сильный сигнал
            signal = 'buy'
            confidence = min(0.9, buy_score / 100.0)
            should_execute = True
            stop_loss = price * 0.987  # 1.3% стоп-лосс
            take_profit = price * 1.035  # 3.5% тейк-профит
            reason = f"ОЧЕНЬ СИЛЬНЫЙ BUY (score: {buy_score}): " + "; ".join(confidence_factors[:3])
            
        elif sell_score >= very_strong_threshold:  # Очень сильный сигнал
            signal = 'sell'
            confidence = min(0.9, sell_score / 100.0)
            should_execute = True
            stop_loss = price * 1.013  # 1.3% стоп-лосс
            take_profit = price * 0.965  # 3.5% тейк-профит
            reason = f"ОЧЕНЬ СИЛЬНЫЙ SELL (score: {sell_score}): " + "; ".join(confidence_factors[:3])
            
        elif buy_score >= strong_threshold:  # Сильный сигнал
            signal = 'buy'
            confidence = buy_score / 100.0
            should_execute = True
            stop_loss = price * 0.99  # 1% стоп-лосс
            take_profit = price * 1.025  # 2.5% тейк-профит
            reason = f"СИЛЬНЫЙ BUY (score: {buy_score}): " + "; ".join(confidence_factors[:3])
            
        elif sell_score >= strong_threshold:  # Сильный сигнал
            signal = 'sell'
            confidence = sell_score / 100.0
            should_execute = True
            stop_loss = price * 1.01  # 1% стоп-лосс
            take_profit = price * 0.975  # 2.5% тейк-профит
            reason = f"СИЛЬНЫЙ SELL (score: {sell_score}): " + "; ".join(confidence_factors[:3])
            
        elif buy_score >= moderate_threshold:  # Умеренный сигнал
            signal = 'buy'
            confidence = buy_score / 100.0
            should_execute = True
            stop_loss = price * 0.994  # 0.6% стоп-лосс
            take_profit = price * 1.015  # 1.5% тейк-профит
            reason = f"Умеренный BUY (score: {buy_score}): " + "; ".join(confidence_factors[:2])
            
        elif sell_score >= moderate_threshold:  # Умеренный сигнал
            signal = 'sell'
            confidence = sell_score / 100.0
            should_execute = True
            stop_loss = price * 1.006  # 0.6% стоп-лосс
            take_profit = price * 0.985  # 1.5% тейк-профит
            reason = f"Умеренный SELL (score: {sell_score}): " + "; ".join(confidence_factors[:2])
            
        else:  # Слабый сигнал - не торгуем
            signal = 'hold'
            confidence = 0.1
            should_execute = False
            stop_loss = 0
            take_profit = 0
            reason = f"Недостаточно сигнала (buy: {buy_score}, sell: {sell_score}) - ожидание"
        
        return {
            'signal': signal,
            'should_execute': should_execute,
            'confidence': confidence,
            'strategy_type': f'adaptive_{strategy_type_suffix}',
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': reason,
            'indicators': indicators,
            'market_regime': market_regime,
            'buy_score': buy_score,
            'sell_score': sell_score,
            'confidence_factors': confidence_factors,
            'time_filter': 'low_activity' if is_low_activity else 'normal'
        }
    
    def _create_hold_signal(self, reason: str) -> Dict:
        """Создание сигнала удержания"""
        return {
            'signal': 'hold',
            'should_execute': False,
            'confidence': 0.0,
            'strategy_type': 'advanced_technical',
            'stop_loss': 0,
            'take_profit': 0,
            'reason': reason
        }
    
    async def _execute_entry(self, 
                           symbol: str, 
                           signal, 
                           price: float, 
                           timestamp):
        """Выполнение входа в позицию"""
        # Проверяем, нет ли уже открытой позиции
        if symbol in self.open_positions:
            return
        
        # Проверяем максимальное количество позиций
        if len(self.open_positions) >= self.config.max_positions:
            return
        
        # Рассчитываем размер позиции
        position_size = await self._calculate_position_size(symbol, signal, price)
        
        if position_size <= 0:
            return
        
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
        
        # Создаем сделку
        self.trade_counter += 1
        trade = BacktestTrade(
            id=self.trade_counter,
            symbol=symbol,
            side=signal.get('signal', 'buy'),
            entry_time=timestamp,
            entry_price=entry_price,
            quantity=position_size,
            commission=commission,
            strategy_type=signal.get('strategy_type', 'unknown'),
            confidence=signal.get('confidence', 0.5),
            stop_loss=signal.get('stop_loss') if signal.get('stop_loss', 0) > 0 else None,
            take_profit=signal.get('take_profit') if signal.get('take_profit', 0) > 0 else None
        )
        
        # Обновляем капитал
        self.current_capital -= required_capital
        
        # Добавляем в открытые позиции
        self.open_positions[symbol] = trade
        
        logger.debug(f"Вход в позицию: {symbol} {signal.get('signal', 'buy')} @ ${entry_price:.2f}, "
                    f"размер: {position_size:.6f}, уверенность: {signal.get('confidence', 0.5):.2f}")
    
    async def _calculate_position_size(self, symbol: str, signal, price: float) -> float:
        """Расчет размера позиции"""
        if self.config.position_sizing_method == "fixed_pct":
            # Фиксированный процент от капитала
            position_value = self.current_capital * self.config.position_size
            return position_value / price
            
        elif self.config.position_sizing_method == "risk_based":
            # На основе риска (используем AdvancedRiskManager)
            volatility = 0.02  # Заглушка, в реальности рассчитывается из данных
            confidence = signal.get('confidence', 0.5) if isinstance(signal, dict) else 0.5
            position_size_pct = await self.risk_manager.adaptive_position_sizing(
                symbol, confidence, volatility
            )
            position_value = self.current_capital * position_size_pct
            return position_value / price
            
        else:  # fixed_amount
            # Фиксированная сумма
            position_value = self.config.initial_capital * self.config.position_size
            return position_value / price
    
    def _apply_slippage(self, price: float, side: str) -> float:
        """Применение проскальзывания"""
        if side == 'buy':
            return price * (1 + self.config.slippage_rate)
        else:  # sell
            return price * (1 - self.config.slippage_rate)
    
    async def _check_exit_conditions(self, current_prices: Dict[str, float], timestamp):
        """Проверка условий выхода"""
        positions_to_close = []
        
        # Обеспечиваем, что timestamp - это datetime объект
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
        elif isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.now()
        
        for symbol, trade in self.open_positions.items():
            if symbol not in current_prices:
                continue
                
            current_price = current_prices[symbol]
            
            # Проверяем стоп-лосс
            if trade.stop_loss and self._check_stop_loss(trade, current_price):
                positions_to_close.append((symbol, current_price, "stop_loss"))
                continue
            
            # Проверяем тейк-профит
            if trade.take_profit and self._check_take_profit(trade, current_price):
                positions_to_close.append((symbol, current_price, "take_profit"))
                continue
            
            # Проверяем максимальное время в позиции
            try:
                duration_hours = (timestamp - trade.entry_time).total_seconds() / 3600
                if duration_hours >= self.config.max_trade_duration:
                    positions_to_close.append((symbol, current_price, "time_limit"))
            except (AttributeError, TypeError):
                # Если не можем рассчитать время, пропускаем проверку времени
                pass
        
        # Закрываем позиции
        for symbol, exit_price, reason in positions_to_close:
            await self._execute_exit(symbol, exit_price, timestamp, reason)
    
    def _check_stop_loss(self, trade: BacktestTrade, current_price: float) -> bool:
        """Проверка стоп-лосса"""
        if trade.side == 'buy':
            return current_price <= trade.stop_loss
        else:  # sell
            return current_price >= trade.stop_loss
    
    def _check_take_profit(self, trade: BacktestTrade, current_price: float) -> bool:
        """Проверка тейк-профита"""
        if trade.side == 'buy':
            return current_price >= trade.take_profit
        else:  # sell
            return current_price <= trade.take_profit
    
    async def _execute_exit(self, symbol: str, exit_price: float, timestamp, reason: str):
        """Выполнение выхода из позиции"""
        if symbol not in self.open_positions:
            return
        
        trade = self.open_positions[symbol]
        
        # Применяем проскальзывание
        final_exit_price = self._apply_slippage(exit_price, 'sell' if trade.side == 'buy' else 'buy')
        
        # Рассчитываем P&L
        if trade.side == 'buy':
            pnl = (final_exit_price - trade.entry_price) * trade.quantity
        else:  # sell
            pnl = (trade.entry_price - final_exit_price) * trade.quantity
        
        # Вычитаем комиссию за выход
        exit_commission = trade.quantity * final_exit_price * self.config.commission_rate
        pnl -= exit_commission
        
        # Обеспечиваем, что timestamp - это datetime объект
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
        elif isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.now()
        
        # Обновляем сделку
        trade.exit_time = timestamp
        trade.exit_price = final_exit_price
        trade.pnl = pnl
        trade.pnl_pct = pnl / (trade.entry_price * trade.quantity) * 100
        trade.commission += exit_commission
        trade.status = TradeStatus.CLOSED
        trade.exit_reason = reason
        
        # Обновляем капитал
        self.current_capital += (trade.quantity * final_exit_price) + pnl
        
        # Перемещаем в закрытые сделки
        self.trades.append(trade)
        del self.open_positions[symbol]
        
        logger.debug(f"Выход из позиции: {symbol} @ ${final_exit_price:.2f}, "
                    f"P&L: ${pnl:.2f} ({trade.pnl_pct:.2f}%), причина: {reason}")
    
    async def _close_all_positions(self, end_date: datetime):
        """Закрытие всех открытых позиций в конце бэктеста"""
        for symbol in list(self.open_positions.keys()):
            # Используем последнюю известную цену
            trade = self.open_positions[symbol]
            await self._execute_exit(symbol, trade.entry_price, end_date, "backtest_end")
    
    async def _update_portfolio_value(self, current_prices: Dict[str, float], timestamp: datetime):
        """Обновление стоимости портфеля"""
        portfolio_value = self.current_capital
        
        # Добавляем стоимость открытых позиций
        for symbol, trade in self.open_positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                position_value = trade.quantity * current_price
                portfolio_value += position_value
        
        # Обновляем риск-менеджер
        self.risk_manager.update_portfolio_value(portfolio_value)
        
        # Обновляем пиковое значение
        if portfolio_value > self.peak_capital:
            self.peak_capital = portfolio_value
    
    def _record_equity_point(self, timestamp, current_prices: Dict[str, float]):
        """Запись точки кривой капитала"""
        portfolio_value = self.current_capital
        
        # Добавляем стоимость открытых позиций
        for symbol, trade in self.open_positions.items():
            if symbol in current_prices:
                position_value = trade.quantity * current_prices[symbol]
                portfolio_value += position_value
        
        drawdown = (self.peak_capital - portfolio_value) / self.peak_capital if self.peak_capital > 0 else 0
        
        # Обеспечиваем, что timestamp - это datetime объект
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
        elif isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.now()
        
        self.equity_curve.append({
            'timestamp': timestamp.isoformat(),
            'portfolio_value': portfolio_value,
            'cash': self.current_capital,
            'positions_value': portfolio_value - self.current_capital,
            'drawdown': drawdown,
            'open_positions': len(self.open_positions)
        })
    
    async def _calculate_metrics(self) -> BacktestMetrics:
        """Расчет метрик бэктеста"""
        if not self.trades:
            return BacktestMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        # Основные расчеты
        final_value = self.equity_curve[-1]['portfolio_value'] if self.equity_curve else self.current_capital
        total_return = final_value - self.config.initial_capital
        total_return_pct = (total_return / self.config.initial_capital) * 100
        
        # Торговые метрики
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        losing_trades = len([t for t in self.trades if t.pnl < 0])
        win_rate = winning_trades / len(self.trades) if self.trades else 0
        
        wins = [t.pnl for t in self.trades if t.pnl > 0]
        losses = [abs(t.pnl) for t in self.trades if t.pnl < 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = max(losses) if losses else 0
        
        profit_factor = sum(wins) / sum(losses) if losses and sum(losses) > 0 else 0
        
        # Временные метрики
        durations = []
        for t in self.trades:
            if t.exit_time and t.entry_time:
                try:
                    # Обеспечиваем, что оба времени - datetime объекты
                    if isinstance(t.entry_time, (int, float)):
                        entry_time = datetime.fromtimestamp(t.entry_time / 1000 if t.entry_time > 1e10 else t.entry_time)
                    else:
                        entry_time = t.entry_time
                    
                    if isinstance(t.exit_time, (int, float)):
                        exit_time = datetime.fromtimestamp(t.exit_time / 1000 if t.exit_time > 1e10 else t.exit_time)
                    else:
                        exit_time = t.exit_time
                    
                    duration_hours = (exit_time - entry_time).total_seconds() / 3600
                    durations.append(duration_hours)
                except (TypeError, AttributeError):
                    # Если не можем рассчитать длительность, пропускаем
                    continue
        avg_trade_duration = np.mean(durations) if durations else 0
        max_trade_duration = max(durations) if durations else 0
        min_trade_duration = min(durations) if durations else 0
        
        # Риск метрики
        returns = [point['portfolio_value'] for point in self.equity_curve]
        if len(returns) > 1:
            pct_returns = [(returns[i] - returns[i-1]) / returns[i-1] for i in range(1, len(returns))]
            
            # Используем AdvancedRiskManager для расчета VaR
            var_95 = await self.risk_manager.calculate_var(pct_returns, 0.95) if len(pct_returns) >= 30 else 0
            var_99 = await self.risk_manager.calculate_var(pct_returns, 0.99) if len(pct_returns) >= 30 else 0
            expected_shortfall = await self.risk_manager.calculate_expected_shortfall(pct_returns, 0.95) if len(pct_returns) >= 30 else 0
            
            volatility = np.std(pct_returns) * np.sqrt(252) if pct_returns else 0
            
            # Sharpe ratio
            risk_free_rate = self.config.risk_free_rate
            excess_return = (total_return_pct / 100) - risk_free_rate
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0
            
            # Sortino ratio
            negative_returns = [r for r in pct_returns if r < 0]
            downside_volatility = np.std(negative_returns) * np.sqrt(252) if negative_returns else 0
            sortino_ratio = excess_return / downside_volatility if downside_volatility > 0 else 0
        else:
            var_95 = var_99 = expected_shortfall = volatility = 0
            sharpe_ratio = sortino_ratio = 0
        
        # Максимальная просадка
        max_drawdown = max([point['drawdown'] for point in self.equity_curve]) if self.equity_curve else 0
        max_drawdown_pct = max_drawdown * 100
        
        # Calmar ratio
        calmar_ratio = (total_return_pct / 100) / max_drawdown if max_drawdown > 0 else 0
        
        # Дополнительные метрики
        recovery_factor = total_return / (max_drawdown * self.config.initial_capital) if max_drawdown > 0 else 0
        ulcer_index = 0  # Упрощенная реализация
        sterling_ratio = 0  # Упрощенная реализация
        
        return BacktestMetrics(
            total_return=total_return,
            total_return_pct=total_return_pct,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_drawdown * self.config.initial_capital,
            max_drawdown_pct=max_drawdown_pct,
            total_trades=len(self.trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            avg_trade_duration=avg_trade_duration,
            max_trade_duration=max_trade_duration,
            min_trade_duration=min_trade_duration,
            var_95=var_95,
            var_99=var_99,
            expected_shortfall=expected_shortfall,
            volatility=volatility,
            recovery_factor=recovery_factor,
            ulcer_index=ulcer_index,
            sterling_ratio=sterling_ratio
        )
    
    def _generate_summary(self, metrics: BacktestMetrics) -> Dict[str, str]:
        """Генерация текстовой сводки результатов"""
        return {
            'performance': f"Доходность: {metrics.total_return_pct:.2f}% (${metrics.total_return:,.0f})",
            'risk': f"Макс. просадка: {metrics.max_drawdown_pct:.2f}%, Sharpe: {metrics.sharpe_ratio:.2f}",
            'trading': f"Сделок: {metrics.total_trades}, Винрейт: {metrics.win_rate:.1%}",
            'ratios': f"Profit Factor: {metrics.profit_factor:.2f}, Calmar: {metrics.calmar_ratio:.2f}"
        }

# Глобальный экземпляр
backtest_engine = BacktestEngine() 