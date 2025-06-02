// Моковые данные для демонстрации веб-интерфейса

export const mockPerformanceData = {
  recent_signals_24h: 47,
  avg_confidence_24h: 0.873,
  buy_signals_24h: 28,
  sell_signals_24h: 19,
  current_profile: 'moderate',
  current_ai_mode: 'semi_auto'
};

export const mockModelsStatus = {
  models: {
    lstm: {
      status: 'trained',
      accuracy: 0.873,
      last_training: '2 часа назад',
      epochs: 50
    },
    cnn: {
      status: 'trained', 
      accuracy: 0.821,
      last_training: '2 часа назад',
      epochs: 50
    },
    weights: {
      lstm: 0.6,
      cnn: 0.4
    }
  }
};

export const mockRecentSignals = {
  signals: [
    {
      id: '1',
      symbol: 'BTC/USDT',
      signal: 'buy',
      confidence: 0.89,
      timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
      source: 'combined',
      metadata: {
        profile: 'moderate',
        ai_mode: 'semi_auto',
        threshold: 0.7,
        recommendation: 'Сильный восходящий тренд с высокой вероятностью продолжения'
      }
    },
    {
      id: '2',
      symbol: 'ETH/USDT',
      signal: 'hold',
      confidence: 0.65,
      timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      source: 'lstm',
      metadata: {
        profile: 'moderate',
        ai_mode: 'semi_auto',
        threshold: 0.7,
        recommendation: 'Боковое движение, ожидание более четкого сигнала'
      }
    },
    {
      id: '3',
      symbol: 'BNB/USDT',
      signal: 'sell',
      confidence: 0.78,
      timestamp: new Date(Date.now() - 1000 * 60 * 25).toISOString(),
      source: 'cnn',
      metadata: {
        profile: 'moderate',
        ai_mode: 'semi_auto',
        threshold: 0.7,
        recommendation: 'Медвежий паттерн на графике, рекомендуется фиксация прибыли'
      }
    }
  ]
};

export const mockSettings = {
  profile: 'moderate',
  ai_mode: 'semi_auto',
  data_source: 'demo',
  cache_ttl: 600,
  auto_cleanup: true
};

export const mockPredictionData = {
  models: {
    lstm: {
      confidence: 0.85,
      probability: 0.78,
      signal: 'buy',
      sequence_length: 60,
      error: false
    },
    cnn: {
      confidence: 0.72,
      pattern: 'bullish_engulfing',
      last_candle_type: 'bullish',
      trend_strength: 0.68,
      error: false
    }
  },
  combined: {
    confidence: 0.79,
    signal: 'buy',
    recommendation: 'Комбинированный анализ указывает на покупку с умеренным риском'
  }
}; 