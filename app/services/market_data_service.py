"""
Сервис получения рыночных данных
Поддерживает несколько источников данных: BingX, Binance, Yahoo Finance
"""

import logging
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio
import aiohttp
from enum import Enum

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Источники рыночных данных"""
    BINGX = "bingx"
    BINANCE = "binance"
    YAHOO = "yahoo"
    DEMO = "demo"  # Синтетические данные для демо

class MarketDataService:
    """Сервис получения рыночных данных"""
    
    def __init__(self, default_source: DataSource = DataSource.DEMO):
        self.default_source = default_source
        self.cache = {}
        self.cache_ttl = 300  # 5 минут
        
        # Базовые URL для API
        self.api_urls = {
            DataSource.BINGX: "https://open-api.bingx.com",
            DataSource.BINANCE: "https://api.binance.com",
            DataSource.YAHOO: "https://query1.finance.yahoo.com"
        }
        
        logger.info(f"Market Data Service инициализирован с источником: {default_source.value}")
    
    async def get_ohlcv_data(
        self, 
        symbol: str, 
        timeframe: str = "1h", 
        limit: int = 500,
        source: Optional[DataSource] = None
    ) -> pd.DataFrame:
        """
        Получение OHLCV данных
        
        Args:
            symbol: Торговая пара (например, "BTCUSDT")
            timeframe: Таймфрейм (1m, 5m, 15m, 30m, 1h, 4h, 1d)
            limit: Количество свечей
            source: Источник данных
            
        Returns:
            DataFrame с OHLCV данными
        """
        if source is None:
            source = self.default_source
        
        cache_key = f"{symbol}_{timeframe}_{limit}_{source.value}"
        
        # Проверяем кэш
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if (datetime.now() - cached_data['timestamp']).seconds < self.cache_ttl:
                logger.info(f"Возвращаем данные из кэша для {symbol}")
                return cached_data['data']
        
        try:
            if source == DataSource.DEMO:
                data = await self._get_demo_data(symbol, timeframe, limit)
            elif source == DataSource.BINGX:
                data = await self._get_bingx_data(symbol, timeframe, limit)
            elif source == DataSource.BINANCE:
                data = await self._get_binance_data(symbol, timeframe, limit)
            elif source == DataSource.YAHOO:
                data = await self._get_yahoo_data(symbol, timeframe, limit)
            else:
                raise ValueError(f"Неподдерживаемый источник данных: {source}")
            
            # Кэшируем результат
            self.cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now()
            }
            
            logger.info(f"Получено {len(data)} записей для {symbol} из {source.value}")
            return data
            
        except Exception as e:
            logger.error(f"Ошибка получения данных для {symbol}: {e}")
            # Возвращаем демо данные в случае ошибки
            return await self._get_demo_data(symbol, timeframe, limit)
    
    async def _get_demo_data(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Генерация синтетических данных для демо"""
        logger.info(f"Генерируем демо данные для {symbol}")
        
        # Определяем базовую цену в зависимости от символа
        base_prices = {
            'BTCUSDT': 50000,
            'ETHUSDT': 3000,
            'BNBUSDT': 300,
            'ADAUSDT': 0.5,
            'SOLUSDT': 100,
            'DOTUSDT': 7,
            'LINKUSDT': 15,
            'MATICUSDT': 1.2
        }
        
        base_price = base_prices.get(symbol.upper(), 1000)
        
        # Генерируем временные метки
        timeframe_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440
        }
        
        minutes = timeframe_minutes.get(timeframe, 60)
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=minutes * limit)
        
        timestamps = pd.date_range(start=start_time, end=end_time, periods=limit)
        
        # Генерируем реалистичные ценовые данные
        np.random.seed(42)  # Для воспроизводимости
        
        # Создаем тренд с шумом
        trend = np.linspace(0, 0.1, limit)  # Небольшой восходящий тренд
        noise = np.random.normal(0, 0.02, limit)  # 2% волатильность
        
        price_changes = trend + noise
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, base_price * 0.5))  # Минимальная цена
        
        prices = np.array(prices)
        
        # Генерируем OHLC данные
        opens = prices
        closes = prices * (1 + np.random.normal(0, 0.005, limit))  # Небольшие изменения
        highs = np.maximum(opens, closes) * (1 + np.abs(np.random.normal(0, 0.01, limit)))
        lows = np.minimum(opens, closes) * (1 - np.abs(np.random.normal(0, 0.01, limit)))
        volumes = np.random.uniform(100, 10000, limit)
        
        # Создаем DataFrame
        data = pd.DataFrame({
            'timestamp': timestamps,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes
        })
        
        return data
    
    async def _get_bingx_data(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Получение данных с BingX"""
        try:
            # Конвертируем таймфрейм в формат BingX
            timeframe_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '4h': '4h', '1d': '1d'
            }
            
            interval = timeframe_map.get(timeframe, '1h')
            
            url = f"{self.api_urls[DataSource.BINGX]}/openApi/swap/v2/quote/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('code') == 0 and 'data' in data:
                            klines = data['data']
                            
                            df = pd.DataFrame(klines, columns=[
                                'timestamp', 'open', 'high', 'low', 'close', 'volume'
                            ])
                            
                            # Конвертируем типы данных
                            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                            for col in ['open', 'high', 'low', 'close', 'volume']:
                                df[col] = pd.to_numeric(df[col])
                            
                            return df
                        else:
                            raise Exception(f"BingX API error: {data}")
                    else:
                        raise Exception(f"HTTP error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Ошибка получения данных BingX: {e}")
            raise
    
    async def _get_binance_data(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Получение данных с Binance"""
        try:
            # Конвертируем таймфрейм в формат Binance
            timeframe_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '4h': '4h', '1d': '1d'
            }
            
            interval = timeframe_map.get(timeframe, '1h')
            
            url = f"{self.api_urls[DataSource.BINANCE]}/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        klines = await response.json()
                        
                        df = pd.DataFrame(klines, columns=[
                            'timestamp', 'open', 'high', 'low', 'close', 'volume',
                            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                            'taker_buy_quote', 'ignore'
                        ])
                        
                        # Оставляем только нужные колонки
                        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                        
                        # Конвертируем типы данных
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        for col in ['open', 'high', 'low', 'close', 'volume']:
                            df[col] = pd.to_numeric(df[col])
                        
                        return df
                    else:
                        raise Exception(f"HTTP error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Ошибка получения данных Binance: {e}")
            raise
    
    async def _get_yahoo_data(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Получение данных с Yahoo Finance"""
        try:
            # Yahoo Finance использует другой формат символов
            yahoo_symbol = symbol.replace('USDT', '-USD')
            
            # Определяем период
            period_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '4h': '4h', '1d': '1d'
            }
            
            interval = period_map.get(timeframe, '1h')
            
            # Рассчитываем временной диапазон
            if timeframe in ['1m', '5m']:
                period = '7d'
            elif timeframe in ['15m', '30m']:
                period = '60d'
            elif timeframe == '1h':
                period = '730d'
            else:
                period = '2y'
            
            url = f"{self.api_urls[DataSource.YAHOO]}/v8/finance/chart/{yahoo_symbol}"
            params = {
                'interval': interval,
                'period1': int((datetime.now() - timedelta(days=365)).timestamp()),
                'period2': int(datetime.now().timestamp()),
                'includePrePost': 'false'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        chart = data['chart']['result'][0]
                        timestamps = chart['timestamp']
                        quotes = chart['indicators']['quote'][0]
                        
                        df = pd.DataFrame({
                            'timestamp': pd.to_datetime(timestamps, unit='s'),
                            'open': quotes['open'],
                            'high': quotes['high'],
                            'low': quotes['low'],
                            'close': quotes['close'],
                            'volume': quotes['volume']
                        })
                        
                        # Удаляем NaN значения
                        df = df.dropna()
                        
                        # Берем последние записи
                        df = df.tail(limit)
                        
                        return df
                    else:
                        raise Exception(f"HTTP error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Ошибка получения данных Yahoo Finance: {e}")
            raise
    
    async def get_current_price(self, symbol: str, source: Optional[DataSource] = None) -> float:
        """Получение текущей цены"""
        try:
            data = await self.get_ohlcv_data(symbol, "1m", 1, source)
            if not data.empty:
                return float(data['close'].iloc[-1])
            else:
                raise Exception("Нет данных о цене")
        except Exception as e:
            logger.error(f"Ошибка получения текущей цены для {symbol}: {e}")
            # Возвращаем примерную цену для демо
            demo_prices = {
                'BTCUSDT': 50000, 'ETHUSDT': 3000, 'BNBUSDT': 300
            }
            return demo_prices.get(symbol.upper(), 1000)
    
    async def get_multiple_symbols(
        self, 
        symbols: List[str], 
        timeframe: str = "1h", 
        limit: int = 100
    ) -> Dict[str, pd.DataFrame]:
        """Получение данных для нескольких символов"""
        results = {}
        
        tasks = []
        for symbol in symbols:
            task = self.get_ohlcv_data(symbol, timeframe, limit)
            tasks.append((symbol, task))
        
        for symbol, task in tasks:
            try:
                data = await task
                results[symbol] = data
            except Exception as e:
                logger.error(f"Ошибка получения данных для {symbol}: {e}")
                results[symbol] = pd.DataFrame()
        
        return results
    
    def clear_cache(self):
        """Очистка кэша"""
        self.cache.clear()
        logger.info("Кэш рыночных данных очищен")
    
    def get_cache_info(self) -> Dict:
        """Информация о кэше"""
        return {
            'cached_items': len(self.cache),
            'cache_ttl_seconds': self.cache_ttl,
            'default_source': self.default_source.value
        } 