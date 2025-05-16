import pytest
from unittest.mock import patch, MagicMock
from app.services import signal_generation_service

def test_generate_signal_for_asset(monkeypatch):
    # Мокаем все внешние сервисы
    monkeypatch.setattr(signal_generation_service, 'fetch_bingx_prices', lambda asset: [100, 101, 102, 103])
    monkeypatch.setattr(signal_generation_service, 'perform_technical_analysis', lambda prices: {'RSI': 70, 'MACD': 1.2})
    monkeypatch.setattr(signal_generation_service, 'analyze_news_with_hector_rag', lambda text: {'sentiment_score': 0.8, 'affected_assets': ['BTC'], 'summary': 'Positive news'})
    monkeypatch.setattr(signal_generation_service, 'apply_risk_management', lambda *args, **kwargs: {'position_size': 1.0, 'stop_loss': 95.0})
    monkeypatch.setattr(signal_generation_service, 'generate_xai_explanation', lambda data: 'Test explanation')
    
    db = MagicMock()
    result = signal_generation_service.generate_signal_for_asset('BTC/USDT', db)
    assert result is not None
    assert 'asset_pair' in result or hasattr(result, 'asset_pair') 