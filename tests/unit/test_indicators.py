import pytest
import numpy as np
from app.utils import indicators

def test_calculate_rsi():
    prices = np.linspace(100, 110, 20)
    rsi = indicators.calculate_rsi(prices, period=14)
    assert isinstance(rsi, float)
    assert 0 <= rsi <= 100

def test_calculate_macd():
    prices = np.linspace(100, 110, 50)
    macd, signal, hist = indicators.calculate_macd(prices)
    assert isinstance(macd, float)
    assert isinstance(signal, float)
    assert isinstance(hist, float)

def test_calculate_ema():
    prices = np.linspace(100, 110, 20)
    ema = indicators.calculate_ema(prices, period=10)
    assert isinstance(ema, float)

def test_candlestick_pattern():
    ohlc = [
        {'open': 100, 'high': 105, 'low': 99, 'close': 104},
        {'open': 104, 'high': 106, 'low': 103, 'close': 105},
        {'open': 105, 'high': 107, 'low': 104, 'close': 106},
    ]
    pattern = indicators.detect_candlestick_pattern(ohlc)
    assert isinstance(pattern, str) 