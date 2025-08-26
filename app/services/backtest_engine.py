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
    # Новые поля для управления риском/сопровождением
    risk_per_unit: float = 0.0
    partial_taken: bool = False
    partial_scaled_qty: float = 0.0
    trail_stop: Optional[float] = None
    atr_at_entry: float = 0.0

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
    position_sizing_method: str = "risk_based"  # fixed_amount, fixed_pct, risk_based
    position_size: float = 0.02  # 2% от капитала (исп. для fixed_pct/fixed_amount)
    use_stop_loss: bool = True
    use_take_profit: bool = True
    max_trade_duration: int = 24  # часов
    risk_free_rate: float = 0.02  # 2% годовых
    # Новые параметры риска
    max_risk_per_trade: float = 0.01  # риск на сделку (1% капитала)
    atr_period: int = 14
    atr_sl_multiplier: float = 1.4
    atr_tp_multiplier: float = 3.2
    # Параметры трейлинга и частичной фиксации
    enable_trailing: bool = True
    trail_atr_multiplier: float = 1.2
    enable_partial_take_profit: bool = True
    partial_take_profit_r: float = 1.0  # зафиксировать часть на 1.0R
    partial_close_pct: float = 0.5
    move_stop_to_be_on_partial: bool = True

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
        # Охлаждение после резких движений
        self._cooldown_until: Dict[str, datetime] = {}
        # Минимальный кулдаун между входами в ту же сторону
        self._last_entry_time: Dict[tuple, datetime] = {}
        self._min_same_side_cooldown_bars: int = 10
        # Кэш исторических данных для исключения повторных запросов
        self._historical_cache: Dict[str, pd.DataFrame] = {}
        
        logger.info("BacktestEngine инициализирован")
    
    async def run_backtest(self, 
                          strategy_config: StrategyConfig,
                          symbols: List[str],
                          start_date: datetime,
                          end_date: datetime,
                          timeframe: str = "1h",
                          strategy_mode: str = "all",
                          threshold_relax_pct: float = 0.0,
                          trend_thresholds: Dict[str, float] | None = None,
                          donchian_k: int = 20,
                          breakout_volume_min: float = 1.6) -> Dict[str, Any]:
        """
        Запуск полного бэктеста
        """
        try:
            logger.info(f"🚀 Запуск бэктеста: {len(symbols)} символов, "
                       f"{start_date.date()} - {end_date.date()}")
            
            # Инициализация
            await self._initialize_backtest(strategy_config)
            # Устанавливаем уровень ослабления порогов для текущего прогона
            self._threshold_relax_pct = max(0.0, min(0.9, float(threshold_relax_pct)))
            self._trend_thresholds = trend_thresholds or {'adx_min': 10.0, 'bb_width_min': 0.015, 'volume_ratio_min': 1.2}
            self._current_timeframe = timeframe
            self._donchian_k = max(5, int(donchian_k))
            self._breakout_volume_min = float(breakout_volume_min)
            # Настройка кулдауна по таймфрейму (минимальный интервал между входами в одну сторону)
            if timeframe == '15m':
                self._min_same_side_cooldown_bars = 12  # ~3 часа
            elif timeframe == '5m':
                self._min_same_side_cooldown_bars = 15  # ~75 минут
            else:
                self._min_same_side_cooldown_bars = 8   # дефолт для более высоких ТФ
            
            # Генерация исторических данных
            historical_data = await self._generate_historical_data(symbols, start_date, end_date, timeframe)
            # Сохраняем в кэш, чтобы не дергать BingX на каждом баре
            self._historical_cache = historical_data
            
            # Основной цикл бэктеста
            await self._run_backtest_loop(historical_data, symbols, timeframe, strategy_mode)
            
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
                               timeframe: str,
                               strategy_mode: str):
        """Основной цикл бэктеста"""
        # Получаем все временные метки и создаем правильный datetime индекс
        all_timestamps = []
        for symbol, data in historical_data.items():
            if len(data) > 0:
                # Если индекс не datetime, создаем его из timestamp колонки или позиции
                if not isinstance(data.index, pd.DatetimeIndex):
                    if 'timestamp' in data.columns:
                        # Используем колонку timestamp
                        data = data.copy()
                        data['timestamp'] = pd.to_datetime(data['timestamp'])
                        data.set_index('timestamp', inplace=True)
                        historical_data[symbol] = data
                    else:
                        # Создаем datetime индекс на основе позиции и таймфрейма
                        tf_minutes = {'1m': 1, '5m': 5, '15m': 15, '30m': 30, '1h': 60, '4h': 240, '1d': 1440}
                        minutes = tf_minutes.get(timeframe, 60)
                        start_time = datetime.now() - timedelta(minutes=len(data) * minutes)
                        timestamps = [start_time + timedelta(minutes=i * minutes) for i in range(len(data))]
                        data = data.copy()
                        data.index = pd.DatetimeIndex(timestamps)
                        historical_data[symbol] = data
                
                all_timestamps.extend(data.index.tolist())
        
        # Убираем дубликаты и сортируем
        all_timestamps = sorted(list(set(all_timestamps)))
        
        for i, ts_val in enumerate(all_timestamps):
            # Обеспечиваем, что timestamp_dt всегда является datetime объектом
            if isinstance(ts_val, pd.Timestamp):
                timestamp_dt = ts_val.to_pydatetime()
            elif isinstance(ts_val, (int, float)):
                if ts_val <= 0 or ts_val < 1e9:  # Invalid timestamp (e.g., 0 or very small)
                    logger.warning(f"⚠️ Некорректный timestamp в _run_backtest_loop: {ts_val}, используем текущее время")
                    timestamp_dt = datetime.now()
                else:
                    # Assume milliseconds if large, otherwise seconds
                    timestamp_dt = datetime.fromtimestamp(ts_val / 1000 if ts_val > 1e10 else ts_val)
            elif isinstance(ts_val, datetime):
                timestamp_dt = ts_val
            else:
                logger.warning(f"⚠️ Неизвестный тип timestamp в _run_backtest_loop: {type(ts_val)}, используем текущее время")
                timestamp_dt = datetime.now()
            
            # Обновляем текущие цены
            current_prices = {}
            for symbol in symbols:
                if ts_val in historical_data[symbol].index:
                    current_prices[symbol] = historical_data[symbol].loc[ts_val, 'close']
            
            # Обновляем стоимость портфеля
            await self._update_portfolio_value(current_prices, timestamp_dt)
            
            # Проверяем стоп-лоссы и тейк-профиты
            await self._check_exit_conditions(current_prices, timestamp_dt)
            
            # Генерируем сигналы (максимальная частота для ультра-агрессивной торговли)
            if i % 1 == 0:  # Проверяем сигналы КАЖДЫЙ бар (максимальная частота)
                await self._process_signals(symbols, current_prices, timestamp_dt, timeframe, strategy_mode)
            
            # Записываем состояние портфеля
            if i % 10 == 0:  # Записываем каждые 10 баров
                self._record_equity_point(timestamp_dt, current_prices)
    
    async def _process_signals(self, 
                             symbols: List[str], 
                             current_prices: Dict[str, float], 
                             timestamp: datetime, 
                             timeframe: str,
                             strategy_mode: str):
        """Обработка торговых сигналов"""
        for symbol in symbols:
            if symbol not in current_prices:
                continue
                
            try:
                # ВРЕМЕННОЕ ИСПРАВЛЕНИЕ: Используем простую стратегию вместо ML
                # Это исправляет проблему с отсутствием сигналов в бэктесте
                signal = await self._generate_simple_signal(symbol, current_prices[symbol], timestamp, timeframe, strategy_mode)
                
                # Проверяем условия для входа
                if signal and signal.get('should_execute', False) and signal.get('signal') in ['buy', 'sell']:
                    await self._execute_entry(symbol, signal, current_prices[symbol], timestamp)
                    
            except Exception as e:
                logger.error(f"Ошибка обработки сигнала для {symbol}: {e}")
    
    async def _generate_simple_signal(self, symbol: str, price: float, timestamp: datetime, timeframe: str, strategy_mode: str) -> Dict:
        """
        Продвинутая техническая стратегия для увеличения PnL
        Использует множественные индикаторы и адаптивные пороги
        """
        try:
            # Валидация и конвертация timestamp - ДОЛЖНО БЫТЬ ПЕРВЫМ!
            if isinstance(timestamp, (int, float)):
                if timestamp <= 0 or timestamp < 1e9:  # Invalid timestamp
                    logger.warning(f"⚠️ Некорректный timestamp в _generate_simple_signal: {timestamp}, используем текущее время")
                    timestamp = datetime.now()
                else:
                    timestamp = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
            elif isinstance(timestamp, pd.Timestamp):
                timestamp = timestamp.to_pydatetime()
            elif not isinstance(timestamp, datetime):
                logger.warning(f"⚠️ Неизвестный тип timestamp в _generate_simple_signal: {type(timestamp)}, используем текущее время")
                timestamp = datetime.now()
            
            # Очищаем старые cooldown записи для предотвращения ошибок
            if symbol in self._cooldown_until:
                cd_until = self._cooldown_until[symbol]
                if isinstance(cd_until, (int, float)):
                    if cd_until <= 0 or cd_until < 1e9:
                        del self._cooldown_until[symbol]
                    else:
                        self._cooldown_until[symbol] = datetime.fromtimestamp(cd_until / 1000 if cd_until > 1e10 else cd_until)
                elif not isinstance(cd_until, datetime):
                    del self._cooldown_until[symbol]
                # Дополнительная проверка: если cooldown уже истек, удаляем его
                elif isinstance(cd_until, datetime) and timestamp > cd_until:
                    del self._cooldown_until[symbol]
            
            # Получаем исторические данные для расчета индикаторов
            historical_data = await self._get_recent_data_for_analysis(symbol, timestamp, timeframe)
            
            if len(historical_data) < 50:  # Недостаточно данных для анализа
                return self._create_hold_signal("Недостаточно данных для анализа")
            
            # Рассчитываем технические индикаторы
            indicators = self._calculate_technical_indicators(historical_data)
            
            # MTF-фильтр для 15m: требуем подтверждение на 1h (только для режима trend_only)
            if strategy_mode == 'trend_only' and timeframe in ['15m']:
                try:
                    htf = await self._get_recent_data_for_analysis(symbol, timestamp, '1h')
                    if len(htf) >= 50:
                        htf_ind = self._calculate_technical_indicators(htf)
                        ema12_h = htf_ind.get('ema_12', indicators.get('ema_12', price))
                        ema26_h = htf_ind.get('ema_26', indicators.get('ema_26', price))
                        macd_hist_h = htf_ind.get('macd_histogram', 0.0)
                        vol_ratio_h = htf_ind.get('volume_ratio', 1.0)
                        # Если локально бычий контекст, требуем бычье подтверждение на 1h; аналогично для медвежьего
                        if indicators.get('ema_12', price) > indicators.get('ema_26', price):
                            if not (ema12_h > ema26_h and macd_hist_h > 0 and vol_ratio_h >= 1.1):
                                return self._create_hold_signal("HTF(1h) фильтр: нет бычьего подтверждения")
                        elif indicators.get('ema_12', price) < indicators.get('ema_26', price):
                            if not (ema12_h < ema26_h and macd_hist_h < 0 and vol_ratio_h >= 1.1):
                                return self._create_hold_signal("HTF(1h) фильтр: нет медвежьего подтверждения")
                except Exception:
                    # При ошибке MTF-фильтр не блокирует, продолжаем
                    pass
            # Доп. MTF-фильтр для 15m: подтверждение на 4h (EMA и MACD согласованы)
            if strategy_mode == 'trend_only' and timeframe in ['15m']:
                try:
                    h4 = await self._get_recent_data_for_analysis(symbol, timestamp, '4h')
                    if len(h4) >= 50:
                        h4_ind = self._calculate_technical_indicators(h4)
                        ema12_h4 = h4_ind.get('ema_12', indicators.get('ema_12', price))
                        ema26_h4 = h4_ind.get('ema_26', indicators.get('ema_26', price))
                        macd_hist_h4 = h4_ind.get('macd_histogram', 0.0)
                        vol_ratio_h4 = h4_ind.get('volume_ratio', 1.0)
                        if indicators.get('ema_12', price) > indicators.get('ema_26', price):
                            if not (ema12_h4 > ema26_h4 and macd_hist_h4 > 0 and vol_ratio_h4 >= 1.05):
                                return self._create_hold_signal("HTF(4h) фильтр: нет бычьего подтверждения")
                        elif indicators.get('ema_12', price) < indicators.get('ema_26', price):
                            if not (ema12_h4 < ema26_h4 and macd_hist_h4 < 0 and vol_ratio_h4 >= 1.05):
                                return self._create_hold_signal("HTF(4h) фильтр: нет медвежьего подтверждения")
                except Exception:
                    pass
            # MTF-фильтр для 5m: требуем подтверждение на 15m (только для режима trend_only)
            if strategy_mode == 'trend_only' and timeframe in ['5m']:
                try:
                    m15 = await self._get_recent_data_for_analysis(symbol, timestamp, '15m')
                    if len(m15) >= 50:
                        m15_ind = self._calculate_technical_indicators(m15)
                        ema12_m15 = m15_ind.get('ema_12', indicators.get('ema_12', price))
                        ema26_m15 = m15_ind.get('ema_26', indicators.get('ema_26', price))
                        macd_hist_m15 = m15_ind.get('macd_histogram', 0.0)
                        vol_ratio_m15 = m15_ind.get('volume_ratio', 1.0)
                        if indicators.get('ema_12', price) > indicators.get('ema_26', price):
                            if not (ema12_m15 > ema26_m15 and macd_hist_m15 > 0 and vol_ratio_m15 >= 1.1):
                                return self._create_hold_signal("HTF(15m) фильтр: нет бычьего подтверждения")
                        elif indicators.get('ema_12', price) < indicators.get('ema_26', price):
                            if not (ema12_m15 < ema26_m15 and macd_hist_m15 < 0 and vol_ratio_m15 >= 1.1):
                                return self._create_hold_signal("HTF(15m) фильтр: нет медвежьего подтверждения")
                except Exception:
                    pass
            
            # Определяем рыночный режим
            market_regime = self._detect_market_regime(historical_data)
            
            # Генерируем сигнал на основе множественных условий
            # Donchian breakout (K параметризуем) + volume filter — ускоренный путь входа
            try:
                K = getattr(self, '_donchian_k', 20)
                if len(historical_data) >= K:
                    recent = historical_data.tail(K)
                    last_close = float(recent['close'].iloc[-1])
                    last_high = float(recent['high'].iloc[-1]) if 'high' in recent.columns else last_close
                    last_low = float(recent['low'].iloc[-1]) if 'low' in recent.columns else last_close
                    prev_close = float(recent['close'].iloc[-2]) if len(recent) >= 2 else last_close
                    prev_max = float(recent['high'].iloc[:-1].max())
                    prev_min = float(recent['low'].iloc[:-1].min())
                    atr = indicators.get('atr', max(1e-6, last_close * 0.01))
                    # Еще более ослабленные пороги для объёма и импульса
                    volume_ratio_now = float(indicators.get('volume_ratio', 1.0))
                    tr_now = max(abs(last_high - last_low), abs(last_high - prev_close), abs(last_low - prev_close))
                    impulse_ok = tr_now >= 0.8 * atr  # Ослаблено с 1.0 до 0.8
                    vol_ok = (volume_ratio_now >= 0.8) or impulse_ok  # Ослаблено с 1.1 до 0.8
                    
                    # Ослабленные условия пробоя: закрытие выше/ниже предыдущего экстремума
                    # Требуем подтверждение: закрытие 2 баров над/ниже уровня или ретест
                    breakout_up = (last_close > prev_max and recent['close'].iloc[-2] > prev_max)  # два закрытия над максимумом
                    breakout_down = (last_close < prev_min and recent['close'].iloc[-2] < prev_min)  # два закрытия ниже минимума
                    
                    # Логика ретеста: вход на откате к уровню пробоя (ослабленные условия)
                    retest_up = (last_close > prev_min and last_close < prev_max and
                                last_low <= prev_min * 1.01 and  # В пределах 1% от поддержки (увеличено с 0.5%)
                                (volume_ratio_now >= 0.8 or tr_now >= 0.6 * atr))
                    retest_down = (last_close > prev_min and last_close < prev_max and
                                  last_high >= prev_max * 0.99 and  # В пределах 1% от сопротивления (увеличено с 0.5%)
                                  (volume_ratio_now >= 0.8 or tr_now >= 0.6 * atr))
                    # Применим уже рассчитанные MTF-фильтры выше (они могли вернуть hold); здесь просто проверим контекст EMA
                    ema12 = indicators.get('ema_12', last_close)
                    ema26 = indicators.get('ema_26', last_close)
                    if breakout_up and vol_ok and ema12 >= ema26:
                        sl_mult = self.config.atr_sl_multiplier
                        tp_mult = self.config.atr_tp_multiplier
                        return {
                            'signal': 'buy',
                            'should_execute': True,
                            'confidence': 0.55,
                            'strategy_type': 'adaptive_breakout',
                            'stop_loss': max(0.0, last_close - atr * sl_mult),
                            'take_profit': last_close + atr * tp_mult,
                            'reason': 'Donchian breakout up + volume/impulse',
                            'indicators': indicators,
                            'market_regime': market_regime
                        }
                    if breakout_down and vol_ok and ema12 <= ema26:
                        sl_mult = self.config.atr_sl_multiplier
                        tp_mult = self.config.atr_tp_multiplier
                        return {
                            'signal': 'sell',
                            'should_execute': True,
                            'confidence': 0.55,
                            'strategy_type': 'adaptive_breakout',
                            'stop_loss': last_close + atr * sl_mult,
                            'take_profit': max(0.0, last_close - atr * tp_mult),
                            'reason': 'Donchian breakout down + volume/impulse',
                            'indicators': indicators,
                            'market_regime': market_regime
                        }
                    # Ретест логика
                    if retest_up and ema12 >= ema26:
                        sl_mult = self.config.atr_sl_multiplier
                        tp_mult = self.config.atr_tp_multiplier
                        return {
                            'signal': 'buy',
                            'should_execute': True,
                            'confidence': 0.45,  # Немного ниже уверенность для ретеста
                            'strategy_type': 'adaptive_breakout',
                            'stop_loss': max(0.0, last_close - atr * sl_mult),
                            'take_profit': last_close + atr * tp_mult,
                            'reason': 'Donchian retest up + volume/impulse',
                            'indicators': indicators,
                            'market_regime': market_regime
                        }
                    if retest_down and ema12 <= ema26:
                        sl_mult = self.config.atr_sl_multiplier
                        tp_mult = self.config.atr_tp_multiplier
                        return {
                            'signal': 'sell',
                            'should_execute': True,
                            'confidence': 0.45,  # Немного ниже уверенность для ретеста
                            'strategy_type': 'adaptive_breakout',
                            'stop_loss': last_close + atr * sl_mult,
                            'take_profit': max(0.0, last_close - atr * tp_mult),
                            'reason': 'Donchian retest down + volume/impulse',
                            'indicators': indicators,
                            'market_regime': market_regime
                        }
            except Exception:
                pass

            # Если breakout не сработал — используем основную многофакторную логику
            signal_data = self._analyze_multi_indicator_signal(indicators, market_regime, price, timestamp, strategy_mode, symbol)
            
            return signal_data
                
        except Exception as e:
            logger.error(f"Ошибка генерации продвинутого сигнала: {e}")
            return self._create_hold_signal(f"Ошибка анализа: {str(e)}")
    
    async def _get_recent_data_for_analysis(self, symbol: str, timestamp: datetime, timeframe: str) -> pd.DataFrame:
        """Получение последних данных для технического анализа"""
        try:
            # Обеспечиваем, что timestamp - это datetime объект
            if isinstance(timestamp, (int, float)):
                # Проверяем, что timestamp не равен 0 или очень маленькому значению
                if timestamp <= 0 or timestamp < 1e9:  # Меньше 2001 года
                    logger.warning(f"⚠️ Некорректный timestamp для {symbol}: {timestamp}, используем текущее время")
                    timestamp = datetime.now()
                else:
                    timestamp = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
            elif isinstance(timestamp, pd.Timestamp):
                timestamp = timestamp.to_pydatetime()
            elif not isinstance(timestamp, datetime):
                logger.warning(f"⚠️ Неизвестный тип timestamp для {symbol}: {type(timestamp)}, используем текущее время")
                timestamp = datetime.now()
            
            # Сначала пробуем взять из кэша исторических данных
            try:
                tf_map_minutes = { '1m':1, '3m':3, '5m':5, '15m':15, '30m':30, '1h':60, '4h':240 }
                tf_min = tf_map_minutes.get(timeframe, 60)
                bars_target = 1200
                lookback_minutes = tf_min * bars_target
                start_time = timestamp - timedelta(minutes=lookback_minutes)
                cached_df = None
                if hasattr(self, '_historical_cache') and symbol in self._historical_cache:
                    base_df = self._historical_cache.get(symbol)
                    if isinstance(base_df.index, pd.DatetimeIndex):
                        if timeframe == getattr(self, '_current_timeframe', timeframe):
                            cached_df = base_df.loc[(base_df.index >= start_time) & (base_df.index <= timestamp)]
                        else:
                            # Ресемплинг в нужный таймфрейм
                            freq_map = { '1m':'1T','3m':'3T','5m':'5T','15m':'15T','30m':'30T','1h':'1H','4h':'4H' }
                            target_freq = freq_map.get(timeframe, '1H')
                            resampled = base_df.resample(target_freq).agg({
                                'open': 'first',
                                'high': 'max',
                                'low': 'min',
                                'close': 'last',
                                'volume': 'sum'
                            }).dropna()
                            cached_df = resampled.loc[(resampled.index >= start_time) & (resampled.index <= timestamp)]
                if cached_df is not None and len(cached_df) >= 50:
                    return cached_df
            except Exception as e_cache:
                logger.debug(f"Кэш недоступен для {symbol} ({timeframe}): {e_cache}")
            
            # Если кэша недостаточно — пробуем получить реальные данные (ограничиваем частоту вызовов)
            # Пропускаем запрос к реальным данным здесь — полагаемся на кэш.
            # Если кэша не хватает, сразу вернемся к синтетическим данным ниже.
            
        except Exception as e:
            logger.warning(f"❌ Ошибка получения данных для анализа {symbol}: {e}")
        
        # Fallback на синтетические данные
        return await self._generate_synthetic_analysis_data(symbol, timestamp, timeframe)
    
    async def _generate_synthetic_analysis_data(self, symbol: str, timestamp: datetime, timeframe: str) -> pd.DataFrame:
        """Генерация синтетических данных для анализа"""
        # Валидация и конвертация timestamp
        if isinstance(timestamp, (int, float)):
            if timestamp <= 0 or timestamp < 1e9:  # Invalid timestamp
                logger.warning(f"⚠️ Некорректный timestamp в _generate_synthetic_analysis_data: {timestamp}, используем текущее время")
                timestamp = datetime.now()
            else:
                timestamp = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
        elif isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()
        elif not isinstance(timestamp, datetime):
            logger.warning(f"⚠️ Неизвестный тип timestamp в _generate_synthetic_analysis_data: {type(timestamp)}, используем текущее время")
            timestamp = datetime.now()
        
        tf_map_minutes = { '1m':1, '3m':3, '5m':5, '15m':15, '30m':30, '1h':60, '4h':240 }
        tf_min = tf_map_minutes.get(timeframe, 60)
        bars_target = 1200
        lookback_minutes = tf_min * bars_target
        start_time = timestamp - timedelta(minutes=lookback_minutes)
        
        # Создаем временной ряд
        pandas_freq = f"{tf_min}T" if tf_min < 60 else (f"{int(tf_min/60)}H")
        dates = pd.date_range(start=start_time, end=timestamp, freq=pandas_freq)
        
        # Базовая цена для символа
        base_prices = {
            'BTCUSDT': 50000, 'ETHUSDT': 3000, 'ADAUSDT': 1.5,
            'BNBUSDT': 400, 'SOLUSDT': 100, 'XRPUSDT': 0.6
        }
        base_price = base_prices.get(symbol, 1000)
        
        # Генерируем реалистичные данные с трендом
        np.random.seed(hash(f"{symbol}_{timestamp.strftime('%Y%m%d%H%M')}_{timeframe}") % 2**32)
        
        # Создаем тренд с периодическими изменениями
        trend_strength = 0.002  # 0.2% тренд за час
        trend_direction = 1 if (timestamp.minute // max(1,int(tf_min)) % 24) < 12 else -1
        
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
        # Предыдущие значения для кроссовера/ослабления
        if len(macd) >= 2:
            indicators['macd_hist_prev'] = (macd - macd_signal).iloc[-2]
        else:
            indicators['macd_hist_prev'] = indicators['macd_histogram']
        if len(ema_12) >= 2 and len(ema_26) >= 2:
            indicators['ema12_prev'] = ema_12.iloc[-2]
            indicators['ema26_prev'] = ema_26.iloc[-2]
        else:
            indicators['ema12_prev'] = ema_12.iloc[-1]
            indicators['ema26_prev'] = ema_26.iloc[-1]
        
        # Bollinger Bands
        bb_middle = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        indicators['bb_position'] = ((df['close'].iloc[-1] - bb_lower.iloc[-1]) / 
                                   (bb_upper.iloc[-1] - bb_lower.iloc[-1]))
        # Ширина полос Боллинджера (нормированная)
        with pd.option_context('mode.use_inf_as_na', True):
            width_val = (bb_upper - bb_lower).iloc[-1] / max(1e-9, bb_middle.iloc[-1])
        indicators['bb_width'] = float(width_val)
        
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
        # Мгновенное изменение (последний бар)
        indicators['price_change_last'] = df['close'].pct_change().iloc[-1]
        
        # ATR (Wilder)
        period = max(2, self.config.atr_period)
        high = df['high'] if 'high' in df.columns else df['close']
        low = df['low'] if 'low' in df.columns else df['close']
        close = df['close']
        prev_close = close.shift(1)
        tr = pd.concat([
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs()
        ], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        indicators['atr'] = float(atr.iloc[-1])
        
        # ADX (Wilder)
        up_move = high.diff()
        down_move = -low.diff()
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        plus_di = 100 * pd.Series(plus_dm, index=high.index).ewm(alpha=1/period, adjust=False).mean() / atr
        minus_di = 100 * pd.Series(minus_dm, index=low.index).ewm(alpha=1/period, adjust=False).mean() / atr
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)) * 100
        adx = dx.ewm(alpha=1/period, adjust=False).mean()
        indicators['adx'] = float(adx.fillna(0).iloc[-1])
        
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
    
    def _analyze_multi_indicator_signal(self, indicators: Dict, market_regime: str, price: float, timestamp: datetime, strategy_mode: str, symbol: str) -> Dict:
        """Анализ сигнала на основе множественных индикаторов - АДАПТИВНАЯ ВЕРСИЯ"""
        
        # Инициализация счетчиков сигналов
        buy_score = 0
        sell_score = 0
        confidence_factors = []
        signal_type = 'hold'
        
        # ФИЛЬТР КАЧЕСТВА: Проверяем базовые условия рынка
        volatility = indicators.get('volatility', 0.02)
        volume_ratio = indicators.get('volume_ratio', 1.0)
        
        # Отфильтровываем плохие рыночные условия (еще более мягкие фильтры)
        if volatility > 0.15:  # Увеличено с 0.12 до 0.15 - разрешаем еще больше волатильности
            return self._create_hold_signal("Экстремально высокая волатильность для торговли")
        
        if volume_ratio < 0.1:  # Снижено с 0.2 до 0.1 - еще менее строгий фильтр объема
            return self._create_hold_signal("Недостаточный объем для качественного сигнала")
        
        # ВРЕМЕННОЙ ФИЛЬТР: Избегаем периоды низкой активности (сокращен)
        hour = timestamp.hour if hasattr(timestamp, 'hour') else datetime.now().hour
        is_low_activity = hour in [0, 1, 2, 3, 4]  # Усилили ночной фильтр для 5m/15m

        # Тренд-фильтр (режим trend_only) + ADX/BB width
        sma_20 = indicators.get('sma_20', price)
        sma_50 = indicators.get('sma_50', price)
        ema_12 = indicators.get('ema_12', price)
        ema_26 = indicators.get('ema_26', price)
        adx = indicators.get('adx', 0.0)
        bb_width = indicators.get('bb_width', 0.0)
        bb_pos = indicators.get('bb_position', 0.5)
        trend_ok = True
        if strategy_mode == 'trend_only':
            trending = ((price > ema_12 > ema_26 > sma_20) or (price < ema_12 < ema_26 < sma_20))
            tt = getattr(self, '_trend_thresholds', {'adx_min':10.0,'bb_width_min':0.015,'volume_ratio_min':1.2})
            impulse_ok = (adx >= tt.get('adx_min', 10.0)) or (bb_width >= tt.get('bb_width_min', 0.015)) or (volume_ratio >= tt.get('volume_ratio_min', 1.2))
            trend_ok = trending and impulse_ok
        
        # Усиление порогов для SOL
        is_sol = symbol.upper().startswith('SOL')
        rsi = indicators.get('rsi', 50)
        if is_sol:
            # Жёсткий фильтр качества входа для SOL: высокий объём + импульс (ADX/ширина BB)
            entry_quality = (volume_ratio >= 1.6) and (adx >= 15.0 or bb_width >= 0.02)
            if not entry_quality:
                return self._create_hold_signal("SOL: entry quality gate (vol/adx/bb)")
            # Усиление порогов для снижения частоты и повышения качества входов (будет применено ниже после инициализации порогов)
            if rsi > 58:
                buy_score += 5
                confidence_factors.append("RSI>58 (SOL)")
            elif rsi < 42:
                sell_score += 5
                confidence_factors.append("RSI<42 (SOL)")
            if volume_ratio > 1.8:
                if buy_score >= sell_score:
                    buy_score += 5
                else:
                    sell_score += 5
                confidence_factors.append(f"High volume {volume_ratio:.1f}x (SOL)")
        
        # RSI анализ - СБАЛАНСИРОВАННЫЕ ПОРОГИ
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
        
        # Для 15m: торговые окна 6-22 UTC (избегаем низкой активности)
        tf_cur = getattr(self, '_current_timeframe', '1h')
        if tf_cur in ['15m']:
            if hour < 6 or hour > 22:
                return self._create_hold_signal("15m: вне торгового окна 6-22 UTC")
        elif tf_cur in ['1h'] and is_low_activity:
            return self._create_hold_signal("1h: ночной период — входы отключены")
        
        # Охлаждение после резкого движения (>2% за бар) — 2 бара на 15m
        pc_last = indicators.get('price_change_last', 0.0)
        cd_until = self._cooldown_until.get(symbol)
        
        # Валидация cd_until - убеждаемся что это datetime
        if cd_until and not isinstance(cd_until, datetime):
            if isinstance(cd_until, (int, float)):
                if cd_until <= 0 or cd_until < 1e9:
                    cd_until = None
                else:
                    cd_until = datetime.fromtimestamp(cd_until / 1000 if cd_until > 1e10 else cd_until)
            else:
                cd_until = None
        
        if tf_cur in ['15m'] and cd_until and timestamp < cd_until:
            return self._create_hold_signal("Охлаждение после резкого движения")
        if tf_cur in ['15m'] and abs(pc_last) >= 0.02:
            self._cooldown_until[symbol] = timestamp + timedelta(minutes=30)
            return self._create_hold_signal("Резкое движение — охлаждение")
        # Охлаждение на 5m после >2% — 3 бара (15 минут) - увеличен порог
        if tf_cur in ['5m'] and cd_until and timestamp < cd_until:
            return self._create_hold_signal("5m охлаждение после импульса")
        if tf_cur in ['5m'] and abs(pc_last) >= 0.02:  # Увеличено с 0.015 до 0.02
            self._cooldown_until[symbol] = timestamp + timedelta(minutes=20)
            return self._create_hold_signal("5m резкое движение — охлаждение")
        
        # Фильтр конфликтующих сигналов (еще более мягкий)
        signal_conflict = abs(buy_score - sell_score) < 5  # Уменьшено с 8 до 5
        if signal_conflict and max(buy_score, sell_score) < 20:  # Уменьшено с 28 до 20
            # На 15m отключаем лёгкие входы при конфликте — только HOLD
            if getattr(self, '_current_timeframe', '1h') == '15m':
                return self._create_hold_signal("15m: конфликт сигналов — HOLD")
            # Попытка лёгкого сигнала при EMA/объёме на других ТФ
            if ema_12 > ema_26 and volume_ratio >= 1.0:
                buy_score += 15
                confidence_factors.append("Light buy via EMA/volume (conflict)")
            elif ema_12 < ema_26 and volume_ratio >= 1.0:
                sell_score += 15
                confidence_factors.append("Light sell via EMA/volume (conflict)")
            else:
                return self._create_hold_signal("Неопределенные сигналы - ожидание")
        
        # Адаптивные пороги на основе агрессивности стратегии
        # Получаем уровень агрессивности из стратегии (если доступно)
        try:
            aggressiveness = getattr(self.strategy_manager, 'current_aggressiveness', 'MODERATE')
            if hasattr(aggressiveness, 'value'):
                aggressiveness = aggressiveness.value
        except:
            aggressiveness = 'MODERATE'
        
        # Настройка порогов в зависимости от агрессивности (снижены для большего количества сделок)
        if aggressiveness == 'CONSERVATIVE':
            # Консервативные пороги - только очень качественные сигналы
            very_strong_threshold = 40
            strong_threshold = 25
            moderate_threshold = 15
            strategy_type_suffix = 'conservative'
        elif aggressiveness == 'AGGRESSIVE':
            # Агрессивные пороги - больше сделок
            very_strong_threshold = 20
            strong_threshold = 12
            moderate_threshold = 6
            strategy_type_suffix = 'aggressive'
        else:  # MODERATE
            # Сбалансированные пороги
            very_strong_threshold = 30
            strong_threshold = 18
            moderate_threshold = 10
            strategy_type_suffix = 'balanced'

        # Если тренд слабый/не подтверждён, не блокируем, а повышаем пороги
        if not trend_ok:
            very_strong_threshold += 4
            strong_threshold += 8
            moderate_threshold += 8

        # Ослабление порогов (quick/fallback): понижаем на заданный процент
        relax = getattr(self, '_threshold_relax_pct', 0.0)
        if relax > 0:
            very_strong_threshold = max(0, int(round(very_strong_threshold * (1 - relax))))
            strong_threshold = max(0, int(round(strong_threshold * (1 - relax))))
            moderate_threshold = max(0, int(round(moderate_threshold * (1 - relax))))

        # Облегчённый вход при слабом тренде: подтверждение импульса объёмом и EMA раскладкой
        if not trend_ok:
            if ema_12 > ema_26 and volume_ratio >= 1.0:  # Снижено с 1.2 до 1.0
                buy_score += 25  # Увеличено с 20 до 25
                confidence_factors.append("Light entry boost (bull) via EMA/volume")
            elif ema_12 < ema_26 and volume_ratio >= 1.0:  # Снижено с 1.2 до 1.0
                sell_score += 25  # Увеличено с 20 до 25
                confidence_factors.append("Light entry boost (bear) via EMA/volume")
        
        # Ниже — блок определения финального сигнала. Заменим статические SL/TP на ATR-мультипликаторы
        atr = indicators.get('atr', price * 0.01)
        sl_mult = self.config.atr_sl_multiplier
        tp_mult = self.config.atr_tp_multiplier
        # Для 15m/1h слегка увеличим SL и TP, чтобы снизить выбивание по шуму
        if tf_cur in ['15m', '1h']:
            sl_mult *= 1.22
            tp_mult *= 1.14
        
        # Режимно-зависимая корректировка TP/SL
        if market_regime == 'bull_trend':
            sl_mult *= 0.9
            tp_mult *= 1.15
        elif market_regime == 'bear_trend':
            sl_mult *= 1.1
            tp_mult *= 1.08
        elif market_regime == 'high_volatility':
            sl_mult *= 1.2
            tp_mult *= 1.2
        # Доп. увеличение TP для SOL в bull_trend
        if market_regime == 'bull_trend' and symbol.upper().startswith('SOL'):
            tp_mult *= 1.1

        # Небольшое усиление порогов для снижения количества низкокачественных входов
        strong_threshold = int(strong_threshold + 2)
        moderate_threshold = int(moderate_threshold + 2)
        # Доп. усиление для SOL (смещение порогов после инициализации)
        if symbol.upper().startswith('SOL'):
            strong_threshold += 4
            moderate_threshold += 4
        
        # Улучшенные входные условия для 15m (all/trend_only):
        if tf_cur in ['15m']:
            # Минимальная волатильность: ATR/price порог, чтобы отсечь шум
            atr_val = indicators.get('atr', max(1e-6, price * 0.005))
            if atr_val / max(1e-6, price) < 0.0045:
                return self._create_hold_signal("15m: низкая волатильность (ATR/price)")
            # Гейт по EMA/SMA и объёму
            if not ((ema_12 > ema_26 and price > sma_20 and volume_ratio >= 1.6) or (ema_12 < ema_26 and price < sma_20 and volume_ratio >= 1.6)):
                return self._create_hold_signal("15m: условия EMA/SMA/объём не выполнены")
            # MACD + RSI фильтры импульса (ужесточённые)
            macd_hist = indicators.get('macd_histogram', 0.0)
            rsi_val = indicators.get('rsi', 50)
            if ema_12 > ema_26 and not (macd_hist > 0.0 and rsi_val > 50):
                return self._create_hold_signal("15m: слабый импульс для лонга (MACD/RSI)")
            if ema_12 < ema_26 and not (macd_hist < 0.0 and rsi_val < 50):
                return self._create_hold_signal("15m: слабый импульс для шорта (MACD/RSI)")
        
        # Определение финального сигнала - АДАПТИВНЫЕ ПОРОГИ
        if buy_score >= very_strong_threshold:  # Очень сильный сигнал
            signal = 'buy'
            confidence = min(0.9, buy_score / 100.0)
            should_execute = True
            stop_loss = max(0.0, price - atr * sl_mult)
            take_profit = price + atr * tp_mult
            reason = f"ОЧЕНЬ СИЛЬНЫЙ BUY (score: {buy_score}): " + "; ".join(confidence_factors[:3])
        
        elif sell_score >= very_strong_threshold:  # Очень сильный сигнал
            signal = 'sell'
            confidence = min(0.9, sell_score / 100.0)
            should_execute = True
            stop_loss = price + atr * sl_mult
            take_profit = max(0.0, price - atr * tp_mult)
            reason = f"ОЧЕНЬ СИЛЬНЫЙ SELL (score: {sell_score}): " + "; ".join(confidence_factors[:3])
        
        elif buy_score >= strong_threshold:  # Сильный сигнал
            signal = 'buy'
            confidence = buy_score / 100.0
            should_execute = True
            stop_loss = max(0.0, price - atr * sl_mult)
            take_profit = price + atr * tp_mult
            reason = f"СИЛЬНЫЙ BUY (score: {buy_score}): " + "; ".join(confidence_factors[:3])
        
        elif sell_score >= strong_threshold:  # Сильный сигнал
            signal = 'sell'
            confidence = sell_score / 100.0
            should_execute = True
            stop_loss = price + atr * sl_mult
            take_profit = max(0.0, price - atr * tp_mult)
            reason = f"СИЛЬНЫЙ SELL (score: {sell_score}): " + "; ".join(confidence_factors[:3])
        
        elif buy_score >= moderate_threshold:  # Умеренный сигнал
            signal = 'buy'
            confidence = buy_score / 100.0
            should_execute = True
            stop_loss = max(0.0, price - atr * sl_mult)
            take_profit = price + atr * (tp_mult * 0.7)
            reason = f"Умеренный BUY (score: {buy_score}): " + "; ".join(confidence_factors[:2])
        
        elif sell_score >= moderate_threshold:  # Умеренный сигнал
            signal = 'sell'
            confidence = sell_score / 100.0
            should_execute = True
            stop_loss = price + atr * sl_mult
            take_profit = max(0.0, price - atr * (tp_mult * 0.7))
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
        
        # Кулдаун между входами в ту же сторону
        side = signal.get('signal', 'buy') if isinstance(signal, dict) else 'buy'
        tf_min = {'1m':1,'3m':3,'5m':5,'15m':15,'30m':30,'1h':60,'4h':240}.get(getattr(self, '_current_timeframe', '1h'), 60)
        min_delta = timedelta(minutes=self._min_same_side_cooldown_bars * tf_min)
        le_key = (symbol, side)
        last_t = self._last_entry_time.get(le_key)
        if last_t and timestamp < last_t + min_delta:
            return
        
        # Рассчитываем размер позиции
        position_size = await self._calculate_position_size(symbol, signal, price)
        
        if position_size <= 0:
            return
        
        # Применяем комиссию и проскальзывание
        entry_price = self._apply_slippage(price, side)
        commission = position_size * entry_price * self.config.commission_rate
        
        # Проверяем достаточность капитала
        required_capital = position_size * entry_price + commission
        if required_capital > self.current_capital:
            return
        
        # Обеспечиваем, что timestamp - это datetime объект
        if isinstance(timestamp, (int, float)):
            # Проверяем, что timestamp не равен 0 или очень маленькому значению
            if timestamp <= 0 or timestamp < 1e9:  # Меньше 2001 года
                logger.warning(f"⚠️ Некорректный timestamp в _execute_entry: {timestamp}, используем текущее время")
                timestamp = datetime.now()
            else:
                timestamp = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
        elif isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()
        elif not isinstance(timestamp, datetime):
            logger.warning(f"⚠️ Неизвестный тип timestamp в _execute_entry: {type(timestamp)}, используем текущее время")
            timestamp = datetime.now()
        
        # Инициализация стопов/ATR для трейлинга
        stop_loss = signal.get('stop_loss') if isinstance(signal, dict) else None
        take_profit = signal.get('take_profit') if isinstance(signal, dict) else None
        risk_per_unit = 0.0
        if stop_loss and stop_loss > 0:
            risk_per_unit = (entry_price - stop_loss) if side == 'buy' else (stop_loss - entry_price)
            risk_per_unit = max(1e-9, risk_per_unit)
        # Оценка ATR на входе из стоп‑расстояния
        atr_entry = 0.0
        if risk_per_unit > 0 and self.config.atr_sl_multiplier > 0:
            atr_entry = risk_per_unit / self.config.atr_sl_multiplier
        
        # Создаем сделку
        self.trade_counter += 1
        trade = BacktestTrade(
            id=self.trade_counter,
            symbol=symbol,
            side=side,
            entry_time=timestamp,
            entry_price=entry_price,
            quantity=position_size,
            commission=commission,
            strategy_type=signal.get('strategy_type', 'unknown'),
            confidence=signal.get('confidence', 0.5),
            stop_loss=stop_loss if (stop_loss and stop_loss > 0) else None,
            take_profit=take_profit if (take_profit and take_profit > 0) else None,
            risk_per_unit=risk_per_unit,
            trail_stop=stop_loss if (stop_loss and stop_loss > 0) else None,
            atr_at_entry=atr_entry
        )
        
        # Обновляем капитал
        self.current_capital -= required_capital
        
        # Добавляем в открытые позиции
        self.open_positions[symbol] = trade
        # Фиксируем время последнего входа для кулдауна в эту же сторону
        self._last_entry_time[le_key] = timestamp
        
        logger.debug(f"Вход в позицию: {symbol} {side} @ ${entry_price:.2f}, размер: {position_size:.6f}, риск/ед: {risk_per_unit:.6f}")
    
    async def _calculate_position_size(self, symbol: str, signal, price: float) -> float:
        """Расчет размера позиции"""
        if self.config.position_sizing_method == "fixed_pct":
            # Фиксированный процент от капитала
            position_value = self.current_capital * self.config.position_size
            return position_value / price
            
        elif self.config.position_sizing_method == "risk_based":
            # На основе риска (ATR-стоп)
            stop_loss = 0.0
            if isinstance(signal, dict):
                stop_loss = signal.get('stop_loss', 0.0) or 0.0
            risk_per_unit = 0.0
            side = signal.get('signal', 'buy') if isinstance(signal, dict) else 'buy'
            if stop_loss > 0.0:
                if side == 'buy':
                    risk_per_unit = max(1e-9, price - stop_loss)
                else:
                    risk_per_unit = max(1e-9, stop_loss - price)
            if risk_per_unit <= 0:
                # fallback к фиксированному проценту
                position_value = self.current_capital * min(self.config.position_size, 0.05)
                return position_value / price
            # Риск на сделку по таймфрейму
            tf_cur = getattr(self, '_current_timeframe', '1h')
            risk_pct = 0.007 if tf_cur in ['15m'] else (0.005 if tf_cur in ['5m'] else self.config.max_risk_per_trade)
            risk_capital = self.current_capital * risk_pct
            qty = risk_capital / risk_per_unit
            # Ограничение по доступному капиталу
            max_affordable_qty = (self.current_capital * 0.98) / price
            return float(max(0.0, min(qty, max_affordable_qty)))
            
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
            # Проверяем, что timestamp не равен 0 или очень маленькому значению
            if timestamp <= 0 or timestamp < 1e9:  # Меньше 2001 года
                logger.warning(f"⚠️ Некорректный timestamp в _check_exit_conditions: {timestamp}, используем текущее время")
                timestamp = datetime.now()
            else:
                timestamp = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
        elif isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()
        elif not isinstance(timestamp, datetime):
            logger.warning(f"⚠️ Неизвестный тип timestamp в _check_exit_conditions: {type(timestamp)}, используем текущее время")
            timestamp = datetime.now()
        
        for symbol, trade in list(self.open_positions.items()):
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            side = trade.side
            
            # Time-based stop (не достиг 0.5R за N баров): 5m -> 12 баров (~1ч), 15m -> 8 баров (~2ч)
            try:
                tf_cur = getattr(self, '_current_timeframe', '1h')
                duration_hours = (timestamp - trade.entry_time).total_seconds() / 3600
                r_multiple = 0.0
                if trade.risk_per_unit > 0:
                    if side == 'buy':
                        r_multiple = (current_price - trade.entry_price) / trade.risk_per_unit
                    else:
                        r_multiple = (trade.entry_price - current_price) / trade.risk_per_unit
                if tf_cur == '5m' and duration_hours >= 1.0 and r_multiple < 0.5:
                    positions_to_close.append((symbol, current_price, 'time_stop_5m'))
                    continue
                if tf_cur == '15m' and duration_hours >= 2.0 and r_multiple < 0.5:
                    positions_to_close.append((symbol, current_price, 'time_stop_15m'))
                    continue

                # Для SOL на 1h — более строгий тайм-стоп: 12 часов при отсутствии 0.5R
                if tf_cur == '1h' and symbol.upper().startswith('SOL') and duration_hours >= 12.0 and r_multiple < 0.5:
                    positions_to_close.append((symbol, current_price, 'time_stop_SOL_1h'))
                    continue
            except Exception:
                pass
            
            # Ранний выход при ослаблении импульса MACD
            # Для buy: macd_hist становится < 0; для sell: macd_hist > 0
            # RSI/BB край: фиксируем остаток
            try:
                # восстановим индикаторы для последнего бара символа (упрощённо через последний расчёт)
                # в текущей архитектуре индикаторы не кешируются по символу, поэтому этот блок оставляем как заготовку для будущего кеша
                pass
            except Exception:
                pass
            
            # Трейлинг и остальные условия ниже (уже реализованы)
            # Трейлинг‑стоп: обновляем trail_stop на основе ATR при входе (усиленный для 15m)
            tf_cur = getattr(self, '_current_timeframe', '1h')
            trail_mult = (1.6 if (tf_cur not in ['15m'] and symbol.upper().startswith('SOL')) else self.config.trail_atr_multiplier) if tf_cur not in ['15m'] else 1.4
            if self.config.enable_trailing and trade.atr_at_entry > 0:
                if side == 'buy':
                    new_trail = current_price - trail_mult * trade.atr_at_entry
                    trade.trail_stop = max(trade.trail_stop or float('-inf'), new_trail)
                else:
                    new_trail = current_price + trail_mult * trade.atr_at_entry
                    trade.trail_stop = min(trade.trail_stop or float('inf'), new_trail)
            
            # Ступенчатое усиление трейлинга по достижению 1.5R и 2.5R
            if self.config.enable_trailing and trade.risk_per_unit > 0:
                if side == 'buy':
                    current_r = (current_price - trade.entry_price) / trade.risk_per_unit
                else:
                    current_r = (trade.entry_price - current_price) / trade.risk_per_unit
                # Первый апгрейд трейлинга после 1.5R
                if current_r >= 1.5:
                    lvl1 = trade.entry_price + 0.5 * trade.risk_per_unit if side == 'buy' else trade.entry_price - 0.5 * trade.risk_per_unit
                    trade.trail_stop = max(trade.trail_stop or float('-inf'), lvl1) if side == 'buy' else min(trade.trail_stop or float('inf'), lvl1)
                # Второй апгрейд трейлинга после 2.5R
                if current_r >= 2.5:
                    lvl2 = trade.entry_price + 1.0 * trade.risk_per_unit if side == 'buy' else trade.entry_price - 1.0 * trade.risk_per_unit
                    trade.trail_stop = max(trade.trail_stop or float('-inf'), lvl2) if side == 'buy' else min(trade.trail_stop or float('inf'), lvl2)
            
            # Для 5m чуть более широкий трейлинг
            if tf_cur in ['5m'] and trade.atr_at_entry > 0:
                if side == 'buy':
                    new_trail = current_price - 1.5 * trade.atr_at_entry
                    trade.trail_stop = max(trade.trail_stop or float('-inf'), new_trail)
                else:
                    new_trail = current_price + 1.5 * trade.atr_at_entry
                    trade.trail_stop = min(trade.trail_stop or float('inf'), new_trail)
            
            # Частичная фиксация (0.8R на 15m)
            take_pct = self.config.partial_close_pct if tf_cur not in ['15m','5m'] else 0.4
            if self.config.enable_partial_take_profit and not trade.partial_taken and trade.risk_per_unit > 0:
                r_multiple = 0.0
                if side == 'buy':
                    r_multiple = (current_price - trade.entry_price) / trade.risk_per_unit
                else:
                    r_multiple = (trade.entry_price - current_price) / trade.risk_per_unit
                threshold_r = self.config.partial_take_profit_r
                if tf_cur in ['15m']:
                    threshold_r = 0.8
                if tf_cur in ['5m']:
                    threshold_r = 0.6  # ранняя фиксация на 5m
                    take_pct = 0.5
                if r_multiple >= threshold_r:
                    close_qty = trade.quantity * take_pct
                    close_qty = max(0.0, min(close_qty, trade.quantity))
                    if close_qty > 0:
                        # Реализуем P&L на часть позиции
                        exit_price_partial = self._apply_slippage(current_price, 'sell' if side == 'buy' else 'buy')
                        pnl_partial = (exit_price_partial - trade.entry_price) * close_qty if side == 'buy' else (trade.entry_price - exit_price_partial) * close_qty
                        exit_commission = close_qty * exit_price_partial * self.config.commission_rate
                        pnl_partial -= exit_commission
                        self.current_capital += (close_qty * exit_price_partial) + pnl_partial
                        trade.quantity -= close_qty
                        trade.commission += exit_commission
                        trade.pnl += pnl_partial
                        trade.partial_taken = True
                        trade.partial_scaled_qty = close_qty
                        # Перенос стопа в безубыток при частичной фиксации
                        if self.config.move_stop_to_be_on_partial:
                            trade.stop_loss = trade.entry_price
                            trade.trail_stop = trade.entry_price
            
            # Проверяем трейлинг‑стоп
            if trade.trail_stop:
                if (side == 'buy' and current_price <= trade.trail_stop) or (side == 'sell' and current_price >= trade.trail_stop):
                    positions_to_close.append((symbol, current_price, "trailing_stop"))
                    continue
            
            # Проверяем стоп‑лосс
            if trade.stop_loss:
                if (side == 'buy' and current_price <= trade.stop_loss) or (side == 'sell' and current_price >= trade.stop_loss):
                    positions_to_close.append((symbol, current_price, "stop_loss"))
                    continue
            
            # Проверяем тейк‑профит
            if trade.take_profit:
                if (side == 'buy' and current_price >= trade.take_profit) or (side == 'sell' and current_price <= trade.take_profit):
                    positions_to_close.append((symbol, current_price, "take_profit"))
                    continue
            
            # Проверяем максимальное время в позиции
            try:
                duration_hours = (timestamp - trade.entry_time).total_seconds() / 3600
                if duration_hours >= self.config.max_trade_duration:
                    positions_to_close.append((symbol, current_price, "time_limit"))
            except (AttributeError, TypeError):
                # Если не можем рассчитать длительность, пропускаем
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
            # Проверяем, что timestamp не равен 0 или очень маленькому значению
            if timestamp <= 0 or timestamp < 1e9:  # Меньше 2001 года
                logger.warning(f"⚠️ Некорректный timestamp в _execute_exit: {timestamp}, используем текущее время")
                timestamp = datetime.now()
            else:
                timestamp = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
        elif isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()
        elif not isinstance(timestamp, datetime):
            logger.warning(f"⚠️ Неизвестный тип timestamp в _execute_exit: {type(timestamp)}, используем текущее время")
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
            # Проверяем, что timestamp не равен 0 или очень маленькому значению
            if timestamp <= 0 or timestamp < 1e9:  # Меньше 2001 года
                logger.warning(f"⚠️ Некорректный timestamp в _record_equity_point: {timestamp}, используем текущее время")
                timestamp = datetime.now()
            else:
                timestamp = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
        elif isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()
        elif not isinstance(timestamp, datetime):
            logger.warning(f"⚠️ Неизвестный тип timestamp в _record_equity_point: {type(timestamp)}, используем текущее время")
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