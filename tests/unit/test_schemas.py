import pytest
from datetime import datetime
from app.schemas.signal import (
    SignalBase,
    SignalCreate,
    XAIExplanationBase,
    NewsBase,
    NewsRelevance
)

def test_signal_base_validation():
    valid_data = {
        "asset_pair": "BTC/USDT",
        "signal_type": "BUY",
        "confidence_score": 0.85,
        "price_at_signal": 50000.0,
        "time_frame": "1h",
        "technical_indicators": {"RSI": 65.5}
    }
    signal = SignalBase(**valid_data)
    assert signal.asset_pair == "BTC/USDT"
    assert signal.signal_type == "BUY"
    assert signal.confidence_score == 0.85

def test_signal_base_invalid_type():
    invalid_data = {
        "asset_pair": "BTC/USDT",
        "signal_type": "INVALID",
        "confidence_score": 0.85,
        "price_at_signal": 50000.0,
        "time_frame": "1h",
        "technical_indicators": {"RSI": 65.5}
    }
    with pytest.raises(ValueError):
        SignalBase(**invalid_data)

def test_signal_base_invalid_timeframe():
    invalid_data = {
        "asset_pair": "BTC/USDT",
        "signal_type": "BUY",
        "confidence_score": 0.85,
        "price_at_signal": 50000.0,
        "time_frame": "2h",
        "technical_indicators": {"RSI": 65.5}
    }
    with pytest.raises(ValueError):
        SignalBase(**invalid_data)

def test_signal_create_with_xai():
    xai_data = {
        "explanation_text": "RSI indicates oversold conditions",
        "factors_used": {"RSI": 0.7, "MACD": 0.3},
        "model_version": "1.0"
    }
    signal_data = {
        "asset_pair": "BTC/USDT",
        "signal_type": "BUY",
        "confidence_score": 0.85,
        "price_at_signal": 50000.0,
        "time_frame": "1h",
        "technical_indicators": {"RSI": 65.5},
        "xai_explanation": xai_data
    }
    signal = SignalCreate(**signal_data)
    assert signal.xai_explanation is not None
    assert signal.xai_explanation.explanation_text == xai_data["explanation_text"]

def test_news_relevance_validation():
    news_data = {
        "title": "Bitcoin Surges",
        "source": "CryptoNews",
        "published_at": datetime.utcnow(),
        "sentiment_score": 0.8
    }
    relevance_data = {
        "news": news_data,
        "relevance_score": 0.9,
        "impact_type": "POSITIVE"
    }
    relevance = NewsRelevance(**relevance_data)
    assert relevance.relevance_score == 0.9
    assert relevance.impact_type == "POSITIVE"

def test_news_relevance_invalid_impact():
    news_data = {
        "title": "Bitcoin Surges",
        "source": "CryptoNews",
        "published_at": datetime.utcnow(),
        "sentiment_score": 0.8
    }
    invalid_data = {
        "news": news_data,
        "relevance_score": 0.9,
        "impact_type": "INVALID"
    }
    with pytest.raises(ValueError):
        NewsRelevance(**invalid_data) 