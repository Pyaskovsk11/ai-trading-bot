import numpy as np
import pandas as pd
from typing import List, Optional, Dict

def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """
    Рассчитывает RSI (Relative Strength Index) по списку цен.
    Возвращает None, если данных недостаточно.
    """
    if len(prices) < period + 1:
        return None
    series = pd.Series(prices)
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else None

def calculate_ema(prices: List[float], period: int = 21) -> Optional[float]:
    """
    Рассчитывает EMA (Exponential Moving Average) по списку цен.
    Возвращает None, если данных недостаточно.
    """
    if len(prices) < period:
        return None
    series = pd.Series(prices)
    ema = series.ewm(span=period, adjust=False).mean()
    return float(ema.iloc[-1])

def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Dict[str, float]]:
    """
    Рассчитывает MACD и сигнальную линию по списку цен.
    Возвращает словарь с MACD и сигналом, либо None если данных недостаточно.
    """
    if len(prices) < slow + signal:
        return None
    series = pd.Series(prices)
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return {"macd": float(macd.iloc[-1]), "signal": float(signal_line.iloc[-1])}

def detect_candle_pattern(opens: List[float], highs: List[float], lows: List[float], closes: List[float]) -> Optional[str]:
    """
    Простейшее определение свечных моделей (бычье/медвежье поглощение).
    Возвращает название паттерна или None.
    """
    if len(opens) < 2 or len(closes) < 2:
        return None
    # Бычье поглощение
    if closes[-2] < opens[-2] and closes[-1] > opens[-1] and closes[-1] > opens[-2] and opens[-1] < closes[-2]:
        return "Bullish Engulfing"
    # Медвежье поглощение
    if closes[-2] > opens[-2] and closes[-1] < opens[-1] and closes[-1] < opens[-2] and opens[-1] > closes[-2]:
        return "Bearish Engulfing"
    return None 