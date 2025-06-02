"""
BingX Historical Data Service - Сервис для получения реальных исторических данных
Интегрирован с BacktestEngine для замены синтетических данных
"""

import logging
import pandas as pd
import numpy as np
import ccxt
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

@dataclass
class HistoricalDataConfig:
    """Конфигурация для получения исторических данных"""
    api_key: str = ""
    secret_key: str = ""
    sandbox: bool = True
    rate_limit: int = 1200  # requests per minute
    retry_attempts: int = 3
    retry_delay: float = 1.0

class BingXHistoricalDataService:
    """
    Сервис для получения реальных исторических данных с BingX
    """
    
    def __init__(self, config: HistoricalDataConfig = None):
        self.config = config or HistoricalDataConfig()
        self.exchange = None
        self._last_request_time = 0
        self._request_count = 0
        self._rate_limit_window = 60  # 1 minute
        
        # Инициализация BingX exchange
        self._initialize_exchange()
        
        logger.info("BingXHistoricalDataService инициализирован")
    
    def _initialize_exchange(self):
        """Инициализация CCXT exchange"""
        try:
            # Получаем API ключи из переменных окружения
            api_key = os.getenv('BINGX_API_KEY', self.config.api_key)
            secret_key = os.getenv('BINGX_SECRET_KEY', self.config.secret_key)
            
            self.exchange = ccxt.bingx({
                'apiKey': api_key,
                'secret': secret_key,
                'sandbox': self.config.sandbox,
                'enableRateLimit': True,
                'rateLimit': 1000,  # milliseconds between requests
                'options': {
                    'defaultType': 'swap',  # futures by default
                }
            })
            
            logger.info(f"BingX exchange инициализирован (sandbox: {self.config.sandbox})")
            
        except Exception as e:
            logger.warning(f"Не удалось инициализировать BingX exchange: {e}")
            logger.warning("Будут использоваться синтетические данные")
            self.exchange = None
    
    async def _rate_limit_check(self):
        """Проверка и соблюдение rate limit"""
        current_time = time.time()
        
        # Сброс счетчика каждую минуту
        if current_time - self._last_request_time > self._rate_limit_window:
            self._request_count = 0
            self._last_request_time = current_time
        
        # Проверка лимита
        if self._request_count >= self.config.rate_limit:
            sleep_time = self._rate_limit_window - (current_time - self._last_request_time)
            if sleep_time > 0:
                logger.info(f"Rate limit достигнут, ожидание {sleep_time:.1f} секунд")
                await asyncio.sleep(sleep_time)
                self._request_count = 0
                self._last_request_time = time.time()
        
        self._request_count += 1
    
    async def get_historical_data(self, 
                                symbol: str, 
                                start_date: datetime, 
                                end_date: datetime, 
                                timeframe: str = "1h") -> pd.DataFrame:
        """
        Получение исторических данных OHLCV
        
        Args:
            symbol: Торговая пара (например, 'BTCUSDT')
            start_date: Дата начала
            end_date: Дата окончания
            timeframe: Таймфрейм ('1m', '5m', '15m', '1h', '4h', '1d')
            
        Returns:
            DataFrame с колонками: timestamp, open, high, low, close, volume
        """
        try:
            if not self.exchange:
                logger.warning(f"Exchange не инициализирован, генерируем синтетические данные для {symbol}")
                return await self._generate_synthetic_data(symbol, start_date, end_date, timeframe)
            
            logger.info(f"Получение реальных данных BingX: {symbol} {timeframe} "
                       f"{start_date.date()} - {end_date.date()}")
            
            # Конвертируем символ в формат BingX
            bingx_symbol = self._convert_symbol_format(symbol)
            
            # Получаем данные по частям если период большой
            all_data = []
            current_start = start_date
            
            while current_start < end_date:
                # BingX имеет лимит на количество свечей за запрос
                chunk_end = min(current_start + timedelta(days=30), end_date)
                
                chunk_data = await self._fetch_ohlcv_chunk(
                    bingx_symbol, timeframe, current_start, chunk_end
                )
                
                if chunk_data is not None and len(chunk_data) > 0:
                    all_data.extend(chunk_data)
                
                current_start = chunk_end
                
                # Соблюдаем rate limit
                await self._rate_limit_check()
            
            if not all_data:
                logger.warning(f"Не удалось получить данные для {symbol}, используем синтетические")
                return await self._generate_synthetic_data(symbol, start_date, end_date, timeframe)
            
            # Конвертируем в DataFrame
            df = self._convert_to_dataframe(all_data)
            
            # Фильтруем по датам
            df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
            
            logger.info(f"Получено {len(df)} свечей для {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Ошибка получения данных для {symbol}: {e}")
            logger.warning("Переключаемся на синтетические данные")
            return await self._generate_synthetic_data(symbol, start_date, end_date, timeframe)
    
    async def _fetch_ohlcv_chunk(self, 
                                symbol: str, 
                                timeframe: str, 
                                start_date: datetime, 
                                end_date: datetime) -> Optional[List]:
        """Получение чанка OHLCV данных"""
        try:
            since = int(start_date.timestamp() * 1000)
            until = int(end_date.timestamp() * 1000)
            
            # Определяем лимит на основе таймфрейма
            timeframe_minutes = self._timeframe_to_minutes(timeframe)
            max_candles = min(1440, int((end_date - start_date).total_seconds() / 60 / timeframe_minutes))
            
            for attempt in range(self.config.retry_attempts):
                try:
                    # CCXT методы синхронные, не асинхронные
                    ohlcv = self.exchange.fetch_ohlcv(
                        symbol, 
                        timeframe, 
                        since=since,
                        limit=max_candles,
                        params={'until': until}
                    )
                    
                    return ohlcv
                    
                except Exception as e:
                    logger.warning(f"Попытка {attempt + 1} неудачна для {symbol}: {e}")
                    if attempt < self.config.retry_attempts - 1:
                        await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    else:
                        raise e
            
        except Exception as e:
            logger.error(f"Ошибка получения чанка данных: {e}")
            return None
    
    def _convert_symbol_format(self, symbol: str) -> str:
        """Конвертация символа в формат BingX"""
        # BingX использует формат BTC-USDT для фьючерсов
        if 'USDT' in symbol:
            base = symbol.replace('USDT', '')
            return f"{base}-USDT"
        return symbol
    
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Конвертация таймфрейма в минуты"""
        timeframe_map = {
            '1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '2h': 120, '4h': 240, '6h': 360, '8h': 480, '12h': 720,
            '1d': 1440, '3d': 4320, '1w': 10080
        }
        return timeframe_map.get(timeframe, 60)
    
    def _convert_to_dataframe(self, ohlcv_data: List) -> pd.DataFrame:
        """Конвертация OHLCV данных в DataFrame"""
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Конвертируем timestamp в datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Конвертируем цены в float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Сортируем по времени
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    async def _generate_synthetic_data(self, 
                                     symbol: str, 
                                     start_date: datetime, 
                                     end_date: datetime, 
                                     timeframe: str) -> pd.DataFrame:
        """Генерация синтетических данных как fallback"""
        logger.info(f"Генерация синтетических данных для {symbol}")
        
        # Определяем частоту
        freq_map = {
            '1m': '1T', '5m': '5T', '15m': '15T', '30m': '30T',
            '1h': '1H', '4h': '4H', '1d': '1D'
        }
        freq = freq_map.get(timeframe, '1H')
        
        # Создаем временной ряд
        dates = pd.date_range(start=start_date, end=end_date, freq=freq.replace('H', 'h'))
        periods = len(dates)
        
        # Базовая цена (зависит от символа)
        base_prices = {
            'BTCUSDT': 50000, 'ETHUSDT': 3000, 'ADAUSDT': 1.5,
            'BNBUSDT': 400, 'SOLUSDT': 100, 'XRPUSDT': 0.6,
            'DOGEUSDT': 0.08, 'LTCUSDT': 70, 'LINKUSDT': 15
        }
        base_price = base_prices.get(symbol, 1000)
        
        # Генерируем более реалистичные данные
        np.random.seed(hash(symbol) % 2**32)
        
        # Создаем тренд с волатильностью
        trend = np.cumsum(np.random.normal(0, 0.001, periods))  # Случайное блуждание
        volatility = np.random.normal(0, 0.02, periods)  # Дневная волатильность 2%
        
        # Добавляем циклические компоненты (имитация рыночных циклов)
        cycle1 = 0.01 * np.sin(np.linspace(0, 4*np.pi, periods))  # Долгосрочный цикл
        cycle2 = 0.005 * np.sin(np.linspace(0, 20*np.pi, periods))  # Краткосрочный цикл
        
        # Создаем ценовой ряд
        log_prices = np.log(base_price) + trend + volatility + cycle1 + cycle2
        close_prices = np.exp(log_prices)
        
        # Генерируем OHLC на основе close
        high_prices = close_prices * (1 + np.abs(np.random.normal(0, 0.01, periods)))
        low_prices = close_prices * (1 - np.abs(np.random.normal(0, 0.01, periods)))
        
        # Open цена - это close предыдущей свечи (с небольшим гэпом)
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = close_prices[0]
        gap = np.random.normal(0, 0.002, periods)
        open_prices = open_prices * (1 + gap)
        
        # Корректируем high/low
        high_prices = np.maximum(high_prices, np.maximum(open_prices, close_prices))
        low_prices = np.minimum(low_prices, np.minimum(open_prices, close_prices))
        
        # Генерируем объемы (коррелированные с волатильностью)
        base_volume = 1000000
        volume_multiplier = 1 + np.abs(volatility) * 10  # Больше объем при высокой волатильности
        volumes = np.random.uniform(0.5, 2.0, periods) * base_volume * volume_multiplier
        
        # Создаем DataFrame
        df = pd.DataFrame({
            'timestamp': dates,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes
        })
        
        return df
    
    async def get_multiple_symbols_data(self, 
                                      symbols: List[str], 
                                      start_date: datetime, 
                                      end_date: datetime, 
                                      timeframe: str = "1h") -> Dict[str, pd.DataFrame]:
        """
        Получение данных для множественных символов
        
        Args:
            symbols: Список торговых пар
            start_date: Дата начала
            end_date: Дата окончания
            timeframe: Таймфрейм
            
        Returns:
            Словарь {symbol: DataFrame}
        """
        logger.info(f"Получение данных для {len(symbols)} символов")
        
        results = {}
        
        for symbol in symbols:
            try:
                data = await self.get_historical_data(symbol, start_date, end_date, timeframe)
                results[symbol] = data
                
                # Небольшая пауза между запросами
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Ошибка получения данных для {symbol}: {e}")
                # Генерируем синтетические данные как fallback
                results[symbol] = await self._generate_synthetic_data(
                    symbol, start_date, end_date, timeframe
                )
        
        logger.info(f"Получены данные для {len(results)} символов")
        return results
    
    async def validate_symbol(self, symbol: str) -> bool:
        """Проверка доступности символа на бирже"""
        try:
            if not self.exchange:
                return True  # Если exchange недоступен, считаем символ валидным
            
            markets = self.exchange.load_markets()  # Синхронный метод
            bingx_symbol = self._convert_symbol_format(symbol)
            
            return bingx_symbol in markets
            
        except Exception as e:
            logger.warning(f"Ошибка валидации символа {symbol}: {e}")
            return True  # В случае ошибки считаем символ валидным
    
    async def get_available_symbols(self) -> List[str]:
        """Получение списка доступных торговых пар"""
        try:
            if not self.exchange:
                # Возвращаем популярные пары если API недоступен
                return [
                    'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT', 'SOLUSDT',
                    'XRPUSDT', 'DOGEUSDT', 'LTCUSDT', 'LINKUSDT', 'DOTUSDT'
                ]
            
            markets = self.exchange.load_markets()  # Синхронный метод
            
            # Фильтруем только USDT пары для фьючерсов
            usdt_pairs = [
                symbol for symbol in markets.keys() 
                if 'USDT' in symbol and markets[symbol]['type'] == 'swap'
            ]
            
            return sorted(usdt_pairs)
            
        except Exception as e:
            logger.error(f"Ошибка получения списка символов: {e}")
            return ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']  # Fallback список

# Глобальный экземпляр сервиса
bingx_historical_service = BingXHistoricalDataService() 