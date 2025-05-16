from typing import List, Dict, Any, Optional
from app.utils import indicators


def analyze_ohlcv(ohlcv: Dict[str, List[float]]) -> Dict[str, Any]:
    """
    Анализирует OHLCV-данные и возвращает значения индикаторов и свечной паттерн.
    ohlcv: {
        'open': [...], 'high': [...], 'low': [...], 'close': [...], 'volume': [...]
    }
    """
    closes = ohlcv.get('close', [])
    opens = ohlcv.get('open', [])
    highs = ohlcv.get('high', [])
    lows = ohlcv.get('low', [])

    rsi = indicators.calculate_rsi(closes)
    ema = indicators.calculate_ema(closes)
    macd_dict = indicators.calculate_macd(closes)
    candle_pattern = indicators.detect_candle_pattern(opens, highs, lows, closes)

    result = {
        'rsi': rsi,
        'ema': ema,
        'macd': macd_dict['macd'] if macd_dict else None,
        'macd_signal': macd_dict['signal'] if macd_dict else None,
        'candle_pattern': candle_pattern
    }
    return result 