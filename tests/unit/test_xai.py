from app.utils.xai import generate_xai_explanation

def test_generate_xai_explanation_basic():
    signal_data = {
        'asset_pair': 'BTC/USDT',
        'signal_type': 'BUY',
        'technical_indicators': {'RSI': 72, 'MACD': 1.2},
        'news_sentiment': 0.8,
        'smart_money_influence': 0.5
    }
    explanation = generate_xai_explanation(signal_data)
    assert isinstance(explanation, str)
    assert 'BTC/USDT' in explanation
    assert 'RSI' in explanation
    assert 'MACD' in explanation

def test_generate_xai_explanation_negative_sentiment():
    signal_data = {
        'asset_pair': 'ETH/USDT',
        'signal_type': 'SELL',
        'technical_indicators': {'RSI': 28, 'MACD': -1.5},
        'news_sentiment': -0.7,
        'smart_money_influence': -0.3
    }
    explanation = generate_xai_explanation(signal_data)
    assert 'ETH/USDT' in explanation
    assert 'SELL' in explanation
    assert 'отрицательный' in explanation or 'негативный' in explanation 