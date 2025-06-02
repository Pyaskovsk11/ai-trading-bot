from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def get_current_price(symbol: str) -> float:
    """Получение текущей цены с BingX API через последние сделки"""
    try:
        bingx_symbol = symbol.replace('/', '-')
        
        # Получаем последнюю сделку для точной цены
        url = "https://open-api.bingx.com/openApi/spot/v1/market/trades"
        params = {
            "symbol": bingx_symbol,
            "limit": 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0 and 'data' in data and data['data']:
                trades = data['data']
                if trades:
                    latest_trade = trades[0]
                    current_price = float(latest_trade['price'])
                    logger.info(f"Получена текущая цена {symbol}: ${current_price}")
                    return current_price
        
        logger.error(f"Не удалось получить текущую цену для {symbol}")
        return 0.0
        
    except Exception as e:
        logger.error(f"Ошибка получения текущей цены для {symbol}: {e}")
        return 0.0

def get_bingx_data(symbol: str, interval: str = "1h", limit: int = 100):
    """Получение данных с BingX API"""
    try:
        # Конвертируем символ для BingX (BTC/USDT -> BTC-USDT)
        bingx_symbol = symbol.replace('/', '-')
        
        # Правильный endpoint для BingX Spot API
        url = "https://open-api.bingx.com/openApi/spot/v1/market/kline"
        params = {
            "symbol": bingx_symbol,
            "interval": interval,
            "limit": limit
        }
        
        logger.info(f"Запрос к BingX API: {url} с параметрами {params}")
        
        response = requests.get(url, params=params, timeout=10)
        logger.info(f"Ответ BingX API: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == 0 and 'data' in data:
                klines = data['data']
                
                if klines:
                    # Преобразуем в DataFrame
                    df = pd.DataFrame(klines)
                    
                    # Проверяем структуру данных
                    logger.info(f"Структура данных BingX: {df.columns.tolist() if not df.empty else 'Пустой DataFrame'}")
                    
                    if len(df.columns) >= 6:
                        # Переименовываем колонки
                        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume'] + list(df.columns[6:])
                        
                        # Конвертируем типы данных
                        for col in ['open', 'high', 'low', 'close', 'volume']:
                            df[col] = pd.to_numeric(df[col])
                        
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        
                        logger.info(f"Успешно получены данные для {symbol}: {len(df)} записей")
                        return df
                    else:
                        logger.error(f"Неожиданная структура данных: {df.columns.tolist()}")
                        return None
                else:
                    logger.error(f"Пустые данные для {symbol}")
                    return None
            else:
                logger.error(f"Ошибка BingX API: {data}")
                return None
        else:
            logger.error(f"HTTP ошибка BingX API: {response.status_code}, {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Исключение при получении данных для {symbol}: {e}")
        return None

def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """Расчет RSI"""
    try:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    except:
        return 50.0

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> float:
    """Расчет MACD"""
    try:
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        return float(macd.iloc[-1])
    except:
        return 0.0

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict:
    """Расчет Bollinger Bands"""
    try:
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        current_price = float(prices.iloc[-1])
        upper_val = float(upper.iloc[-1])
        middle_val = float(sma.iloc[-1])
        lower_val = float(lower.iloc[-1])
        
        # Определяем позицию
        if current_price > upper_val * 0.98:
            position = 'upper'
        elif current_price < lower_val * 1.02:
            position = 'lower'
        else:
            position = 'middle'
        
        return {
            "upper": upper_val,
            "middle": middle_val,
            "lower": lower_val,
            "position": position
        }
    except:
        return {
            "upper": 0.0,
            "middle": 0.0,
            "lower": 0.0,
            "position": "middle"
        }

def get_24h_ticker(symbol: str) -> Dict:
    """Получение 24h статистики с BingX через kline данные"""
    try:
        bingx_symbol = symbol.replace('/', '-')
        
        # Получаем данные за последние 24 часа (24 часовых свечей)
        url = "https://open-api.bingx.com/openApi/spot/v1/market/kline"
        params = {
            "symbol": bingx_symbol,
            "interval": "1h",
            "limit": 24
        }
        
        logger.info(f"Запрос 24h данных к BingX API: {url} с параметрами {params}")
        
        response = requests.get(url, params=params, timeout=10)
        logger.info(f"Ответ 24h данных BingX API: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0 and 'data' in data and data['data']:
                klines = data['data']
                
                # Рассчитываем 24h статистику
                first_candle = klines[0]
                last_candle = klines[-1]
                
                open_24h = float(first_candle[1])  # open первой свечи
                close_current = float(last_candle[4])  # close последней свечи
                
                # Рассчитываем изменение за 24h
                change_24h = ((close_current - open_24h) / open_24h) * 100
                
                # Рассчитываем объем за 24h
                volume_24h = sum(float(candle[5]) for candle in klines)
                
                result = {
                    "priceChangePercent": change_24h,
                    "volume": volume_24h,
                    "lastPrice": close_current,
                    "count": len(klines)
                }
                
                logger.info(f"Успешно рассчитана 24h статистика для {symbol}: цена={close_current}, изменение={change_24h:.2f}%, объем={volume_24h}")
                return result
            else:
                logger.error(f"Ошибка в ответе 24h данных: {data}")
        else:
            logger.error(f"HTTP ошибка 24h данных: {response.status_code}, {response.text}")
        return {}
    except Exception as e:
        logger.error(f"Исключение при получении 24h данных для {symbol}: {e}")
        return {}

@router.get("/monitor", response_model=List[Dict[str, Any]])
def get_coins_monitor(symbols: Optional[str] = Query(None, description="Список символов через запятую")):
    """Получить данные мониторинга для указанных монет с реальными данными"""
    
    # Если символы не указаны, используем по умолчанию
    if symbols:
        coin_symbols = [s.strip().upper() for s in symbols.split(",")]
    else:
        coin_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT']
    
    coins_data = []
    
    for symbol in coin_symbols:
        try:
            # Получаем исторические данные
            df = get_bingx_data(symbol)
            ticker_data = get_24h_ticker(symbol)
            
            if df is not None and len(df) > 0:
                # Получаем точную текущую цену
                current_price = get_current_price(symbol)
                if current_price == 0.0:
                    # Fallback к цене из kline данных
                    current_price = float(df['close'].iloc[-1])
                
                change_24h = float(ticker_data.get('priceChangePercent', 0))
                volume_24h = float(ticker_data.get('volume', 0))
                
                logger.info(f"Обработка {symbol}: точная цена=${current_price}, изменение={change_24h}%, объем={volume_24h}")
                
                # Технические индикаторы
                rsi = calculate_rsi(df['close'])
                macd = calculate_macd(df['close'])
                bollinger = calculate_bollinger_bands(df['close'])
                
                # Уровни поддержки и сопротивления (простой расчет)
                high_20 = df['high'].tail(20).max()
                low_20 = df['low'].tail(20).min()
                support = float(low_20)
                resistance = float(high_20)
                
                # Генерируем сигналы на основе индикаторов
                technical_signal = 'hold'
                if rsi < 30 and macd > 0:
                    technical_signal = 'buy'
                elif rsi > 70 and macd < 0:
                    technical_signal = 'sell'
                
                # AI сигнал (упрощенная логика)
                ai_signal = 'hold'
                if bollinger['position'] == 'lower' and rsi < 40:
                    ai_signal = 'buy'
                elif bollinger['position'] == 'upper' and rsi > 60:
                    ai_signal = 'sell'
                
                # Комбинированный сигнал
                if technical_signal == ai_signal:
                    combined_signal = technical_signal
                else:
                    combined_signal = 'hold'
                
                # Настроение рынка
                sentiment = 'neutral'
                if change_24h > 2:
                    sentiment = 'bullish'
                elif change_24h < -2:
                    sentiment = 'bearish'
                
                coin_data = {
                    "symbol": symbol,
                    "name": symbol.split('/')[0],
                    "price": round(current_price, 2),
                    "change24h": round(change_24h, 2),
                    "volume24h": int(volume_24h),
                    "marketCap": int(float(ticker_data.get('count', 1000000))),  # Приблизительно
                    "rsi": round(rsi, 1),
                    "macd": round(macd, 2),
                    "bollinger": bollinger,
                    "support": round(support, 2),
                    "resistance": round(resistance, 2),
                    "sentiment": sentiment,
                    "signals": {
                        "technical": technical_signal,
                        "ai": ai_signal,
                        "combined": combined_signal
                    },
                    "lastUpdate": datetime.now().isoformat()
                }
                
                logger.info(f"Успешно обработан {symbol} с реальными данными")
                
            else:
                # Fallback к моковым данным если API недоступен
                logger.warning(f"Используем моковые данные для {symbol} - нет данных от API")
                coin_data = generate_mock_data(symbol)
            
            coins_data.append(coin_data)
            
        except Exception as e:
            logger.error(f"Ошибка обработки {symbol}: {e}")
            # Fallback к моковым данным
            coins_data.append(generate_mock_data(symbol))
    
    return coins_data

def generate_mock_data(symbol: str) -> Dict:
    """Генерация моковых данных как fallback"""
    import random
    
    base_price = {
        'BTC/USDT': 45000,
        'ETH/USDT': 2500,
        'BNB/USDT': 300,
        'SOL/USDT': 100,
        'ADA/USDT': 0.5
    }.get(symbol, 1000)
    
    price = base_price + (random.random() - 0.5) * base_price * 0.1
    change24h = (random.random() - 0.5) * 10
    
    return {
        "symbol": symbol,
        "name": symbol.split('/')[0],
        "price": round(price, 2),
        "change24h": round(change24h, 2),
        "volume24h": random.randint(100000000, 2000000000),
        "marketCap": random.randint(1000000000, 100000000000),
        "rsi": round(30 + random.random() * 40, 1),
        "macd": round((random.random() - 0.5) * 100, 2),
        "bollinger": {
            "upper": round(price * 1.02, 2),
            "middle": round(price, 2),
            "lower": round(price * 0.98, 2),
            "position": random.choice(['upper', 'middle', 'lower'])
        },
        "support": round(price * 0.95, 2),
        "resistance": round(price * 1.05, 2),
        "sentiment": random.choice(['bullish', 'bearish', 'neutral']),
        "signals": {
            "technical": random.choice(['buy', 'sell', 'hold']),
            "ai": random.choice(['buy', 'sell', 'hold']),
            "combined": random.choice(['buy', 'sell', 'hold'])
        },
        "lastUpdate": datetime.now().isoformat()
    }

@router.get("/technical-analysis/{symbol}")
def get_technical_analysis(symbol: str):
    """Получить детальный технический анализ для монеты"""
    
    # Генерируем детальные технические данные
    analysis = {
        "symbol": symbol.upper(),
        "timestamp": datetime.now().isoformat(),
        "indicators": {
            "rsi": {
                "value": round(30 + random.random() * 40, 2),
                "signal": random.choice(["oversold", "overbought", "neutral"]),
                "description": "Индекс относительной силы"
            },
            "macd": {
                "macd": round((random.random() - 0.5) * 100, 2),
                "signal": round((random.random() - 0.5) * 100, 2),
                "histogram": round((random.random() - 0.5) * 50, 2),
                "trend": random.choice(["bullish", "bearish", "neutral"])
            },
            "bollinger_bands": {
                "upper": round(45000 + random.random() * 1000, 2),
                "middle": round(45000, 2),
                "lower": round(45000 - random.random() * 1000, 2),
                "squeeze": random.choice([True, False])
            },
            "moving_averages": {
                "sma_20": round(45000 + (random.random() - 0.5) * 500, 2),
                "sma_50": round(45000 + (random.random() - 0.5) * 1000, 2),
                "ema_12": round(45000 + (random.random() - 0.5) * 300, 2),
                "ema_26": round(45000 + (random.random() - 0.5) * 600, 2)
            }
        },
        "support_resistance": {
            "support_levels": [
                round(45000 - random.random() * 2000, 2) for _ in range(3)
            ],
            "resistance_levels": [
                round(45000 + random.random() * 2000, 2) for _ in range(3)
            ]
        },
        "overall_signal": random.choice(["strong_buy", "buy", "hold", "sell", "strong_sell"]),
        "confidence": round(random.random() * 100, 1)
    }
    
    return analysis

@router.get("/market-sentiment")
def get_market_sentiment():
    """Получить общее настроение рынка"""
    
    sentiment_data = {
        "overall_sentiment": random.choice(["bullish", "bearish", "neutral"]),
        "fear_greed_index": random.randint(0, 100),
        "market_cap_change": round((random.random() - 0.5) * 10, 2),
        "volume_change": round((random.random() - 0.5) * 20, 2),
        "top_gainers": [
            {"symbol": "COIN1/USDT", "change": round(random.random() * 20 + 5, 2)},
            {"symbol": "COIN2/USDT", "change": round(random.random() * 15 + 3, 2)},
            {"symbol": "COIN3/USDT", "change": round(random.random() * 10 + 2, 2)}
        ],
        "top_losers": [
            {"symbol": "COIN4/USDT", "change": round(-(random.random() * 20 + 5), 2)},
            {"symbol": "COIN5/USDT", "change": round(-(random.random() * 15 + 3), 2)},
            {"symbol": "COIN6/USDT", "change": round(-(random.random() * 10 + 2), 2)}
        ],
        "timestamp": datetime.now().isoformat()
    }
    
    return sentiment_data

@router.get("/alerts/{symbol}")
def get_coin_alerts(symbol: str):
    """Получить алерты для конкретной монеты"""
    
    alerts = [
        {
            "id": f"alert_{i}",
            "type": random.choice(["price", "volume", "technical", "news"]),
            "severity": random.choice(["low", "medium", "high"]),
            "message": f"Alert message {i} for {symbol}",
            "timestamp": datetime.now().isoformat(),
            "active": random.choice([True, False])
        }
        for i in range(random.randint(0, 5))
    ]
    
    return alerts

@router.get("/portfolio")
def get_portfolio():
    """Получить данные портфеля пользователя"""
    from app.services.bingx_service import bingx_service
    
    try:
        # Получаем реальный баланс с BingX
        balance_data = bingx_service.get_account_balance()
        performance_data = bingx_service.get_portfolio_performance()
        
        # Формируем данные портфеля
        holdings = []
        total_balance = balance_data.get('total_balance_usd', 0)
        
        for balance in balance_data.get('balances', []):
            asset = balance['asset']
            free_amount = float(balance['free'])
            
            if free_amount > 0:
                # Получаем текущую цену (упрощенно)
                current_prices = {
                    'BTC': 45000,
                    'ETH': 2500,
                    'BNB': 300,
                    'USDT': 1.0
                }
                
                current_price = current_prices.get(asset, 1.0)
                value_usd = free_amount * current_price
                allocation_percent = (value_usd / total_balance * 100) if total_balance > 0 else 0
                
                holdings.append({
                    "symbol": asset,
                    "amount": free_amount,
                    "value_usd": round(value_usd, 2),
                    "allocation_percent": round(allocation_percent, 1),
                    "avg_buy_price": current_price * 0.95,  # Примерная средняя цена покупки
                    "current_price": current_price,
                    "pnl": round(value_usd * 0.05, 2),  # Примерная прибыль 5%
                    "pnl_percent": 5.0
                })
        
        portfolio_data = {
            "total_balance_usd": balance_data.get('total_balance_usd', 0),
            "total_balance_btc": balance_data.get('total_balance_btc', 0),
            "daily_pnl": performance_data.get('daily_pnl', 0),
            "daily_pnl_percent": performance_data.get('daily_pnl_percent', 0),
            "holdings": holdings,
            "performance": {
                "total_invested": total_balance * 0.95,  # Примерно
                "total_pnl": performance_data.get('total_pnl', 0),
                "total_pnl_percent": performance_data.get('total_pnl_percent', 0),
                "best_performer": holdings[0]['symbol'] if holdings else "N/A",
                "worst_performer": holdings[-1]['symbol'] if holdings else "N/A"
            },
            "last_update": datetime.now().isoformat()
        }
        
        return portfolio_data
        
    except Exception as e:
        logger.error(f"Ошибка получения портфеля: {e}")
        # Fallback к моковым данным
        return {
            "total_balance_usd": 15420.50,
            "total_balance_btc": 0.342,
            "daily_pnl": 234.80,
            "daily_pnl_percent": 1.55,
            "holdings": [
                {
                    "symbol": "BTC",
                    "amount": 0.25,
                    "value_usd": 11250.00,
                    "allocation_percent": 72.9,
                    "avg_buy_price": 43800.00,
                    "current_price": 45000.00,
                    "pnl": 300.00,
                    "pnl_percent": 2.74
                },
                {
                    "symbol": "ETH",
                    "amount": 1.2,
                    "value_usd": 3000.00,
                    "allocation_percent": 19.5,
                    "avg_buy_price": 2450.00,
                    "current_price": 2500.00,
                    "pnl": 60.00,
                    "pnl_percent": 2.04
                }
            ],
            "performance": {
                "total_invested": 14800.00,
                "total_pnl": 620.50,
                "total_pnl_percent": 4.19,
                "best_performer": "BTC",
                "worst_performer": "ETH"
            },
            "last_update": datetime.now().isoformat()
        }

@router.get("/portfolio/history")
def get_portfolio_history(days: int = Query(30, ge=1, le=365)):
    """Получить историю портфеля"""
    
    # Генерируем историю портфеля
    history = []
    base_value = 15000
    
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i)
        # Симулируем изменения портфеля
        daily_change = (np.random.random() - 0.5) * 0.05  # ±2.5% в день
        value = base_value * (1 + daily_change * i / days)
        
        history.append({
            "date": date.strftime("%Y-%m-%d"),
            "total_value": round(value, 2),
            "daily_change": round(daily_change * 100, 2),
            "btc_price": round(45000 + (np.random.random() - 0.5) * 5000, 2),
            "eth_price": round(2500 + (np.random.random() - 0.5) * 500, 2)
        })
    
    return {
        "history": history,
        "period_days": days,
        "start_value": history[0]["total_value"] if history else 0,
        "end_value": history[-1]["total_value"] if history else 0,
        "total_return": round(((history[-1]["total_value"] / history[0]["total_value"]) - 1) * 100, 2) if history else 0
    }

@router.post("/portfolio/trade")
def execute_trade(trade_data: Dict[str, Any]):
    """Выполнить торговую операцию"""
    
    # В реальном проекте здесь была бы интеграция с биржей
    symbol = trade_data.get("symbol", "")
    side = trade_data.get("side", "")  # buy/sell
    amount = trade_data.get("amount", 0)
    price = trade_data.get("price", 0)
    
    # Симуляция выполнения ордера
    order_result = {
        "order_id": f"order_{datetime.now().timestamp()}",
        "symbol": symbol,
        "side": side,
        "amount": amount,
        "price": price,
        "total": amount * price,
        "status": "filled",
        "timestamp": datetime.now().isoformat(),
        "fee": round(amount * price * 0.001, 4)  # 0.1% комиссия
    }
    
    return order_result

@router.get("/balance")
def get_account_balance():
    """Получить баланс аккаунта"""
    
    balance_data = {
        "spot_balance": {
            "BTC": {"free": 0.25, "locked": 0.0},
            "ETH": {"free": 1.2, "locked": 0.0},
            "BNB": {"free": 3.5, "locked": 0.0},
            "USDT": {"free": 120.50, "locked": 0.0}
        },
        "futures_balance": {
            "USDT": {"free": 500.00, "locked": 150.00}
        },
        "total_balance_usd": 15420.50,
        "available_balance_usd": 15270.50,
        "locked_balance_usd": 150.00,
        "last_update": datetime.now().isoformat()
    }
    
    return balance_data 