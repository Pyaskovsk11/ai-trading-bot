from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import asyncio

from ..services.deep_learning_engine import DeepLearningEngine
from ..services.market_data_service import MarketDataService, DataSource

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deep-learning", tags=["Deep Learning"])

# Глобальные экземпляры сервисов
dl_engine = DeepLearningEngine()
market_data_service = MarketDataService(default_source=DataSource.DEMO)

# Pydantic модели для API
class TrainingRequest(BaseModel):
    symbol: str = Field(..., description="Торговая пара (например, BTC/USDT)")
    timeframe: str = Field(default="1h", description="Таймфрейм данных")
    epochs: int = Field(default=50, description="Количество эпох обучения")
    days_back: int = Field(default=365, description="Количество дней истории для обучения")

class PredictionRequest(BaseModel):
    symbol: str = Field(..., description="Торговая пара")
    timeframe: str = Field(default="1h", description="Таймфрейм данных")
    periods: int = Field(default=100, description="Количество последних периодов для анализа")

class ModelWeightsUpdate(BaseModel):
    lstm_weight: float = Field(..., ge=0, le=1, description="Вес LSTM модели")
    cnn_weight: float = Field(..., ge=0, le=1, description="Вес CNN модели")

class DataSourceUpdate(BaseModel):
    source: str = Field(..., description="Источник данных: demo, bingx, binance, yahoo")

class TrainingResponse(BaseModel):
    status: str
    message: str
    results: Optional[Dict] = None
    training_time: Optional[str] = None

class PredictionResponse(BaseModel):
    symbol: str
    timestamp: str
    models: Dict
    combined: Dict
    market_data: Optional[Dict] = None

@router.post("/train", response_model=TrainingResponse)
async def train_models(
    request: TrainingRequest,
    background_tasks: BackgroundTasks
):
    """
    Обучение Deep Learning моделей на исторических данных
    """
    try:
        logger.info(f"Начинаем обучение моделей для {request.symbol}")
        
        # Получаем исторические данные через MarketDataService
        timeframe_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440
        }
        minutes_per_day = 1440
        limit = (request.days_back * minutes_per_day) // timeframe_minutes.get(request.timeframe, 60)
        limit = min(limit, 1000)  # Ограничиваем максимальным количеством
        
        data = await market_data_service.get_ohlcv_data(
            symbol=request.symbol.replace('/', ''),  # Убираем слэш для API
            timeframe=request.timeframe,
            limit=limit
        )
        
        if len(data) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно данных для обучения. Получено {len(data)} записей, требуется минимум 100"
            )
        
        # Запускаем обучение
        training_start = datetime.now()
        
        # Инициализируем модели если нужно
        await dl_engine.initialize_models()
        
        # Обучение моделей
        results = await dl_engine.train_models(data, epochs=request.epochs)
        
        training_time = str(datetime.now() - training_start)
        
        if 'error' in results:
            return TrainingResponse(
                status="error",
                message=f"Ошибка обучения: {results['error']}",
                training_time=training_time
            )
        
        return TrainingResponse(
            status="success",
            message=f"Модели успешно обучены на {len(data)} записях",
            results=results,
            training_time=training_time
        )
        
    except Exception as e:
        logger.error(f"Ошибка обучения моделей: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict", response_model=PredictionResponse)
async def get_prediction(request: PredictionRequest):
    """
    Получение предсказания от Deep Learning моделей
    """
    try:
        logger.info(f"Получаем предсказание для {request.symbol}")
        
        # Получаем последние данные через MarketDataService
        data = await market_data_service.get_ohlcv_data(
            symbol=request.symbol.replace('/', ''),  # Убираем слэш для API
            timeframe=request.timeframe,
            limit=request.periods
        )
        
        if len(data) < 20:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно данных для предсказания. Получено {len(data)} записей, требуется минимум 20"
            )
        
        # Получаем предсказание
        prediction = await dl_engine.get_prediction(data, request.symbol)
        
        if 'error' in prediction:
            raise HTTPException(status_code=500, detail=prediction['error'])
        
        # Добавляем информацию о рыночных данных
        market_info = {
            'last_price': float(data['close'].iloc[-1]),
            'price_change_24h': float((data['close'].iloc[-1] - data['close'].iloc[-24]) / data['close'].iloc[-24] * 100) if len(data) >= 24 else 0,
            'volume_24h': float(data['volume'].tail(24).sum()) if len(data) >= 24 else float(data['volume'].sum()),
            'data_points': len(data)
        }
        
        return PredictionResponse(
            symbol=prediction['symbol'],
            timestamp=prediction['timestamp'],
            models=prediction['models'],
            combined=prediction['combined'],
            market_data=market_info
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения предсказания: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/status")
async def get_models_status():
    """
    Получение статуса всех Deep Learning моделей
    """
    try:
        status = dl_engine.get_models_status()
        return {
            "status": "success",
            "models": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса моделей: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/weights")
async def update_model_weights(weights: ModelWeightsUpdate):
    """
    Обновление весов моделей для комбинирования предсказаний
    """
    try:
        # Проверяем, что сумма весов равна 1
        total_weight = weights.lstm_weight + weights.cnn_weight
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Сумма весов должна быть равна 1.0, получено {total_weight}"
            )
        
        new_weights = {
            'lstm': weights.lstm_weight,
            'cnn': weights.cnn_weight
        }
        
        dl_engine.update_model_weights(new_weights)
        
        return {
            "status": "success",
            "message": "Веса моделей обновлены",
            "new_weights": new_weights,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка обновления весов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache")
async def clear_prediction_cache():
    """
    Очистка кэша предсказаний
    """
    try:
        dl_engine.clear_cache()
        return {
            "status": "success",
            "message": "Кэш предсказаний очищен",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка очистки кэша: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/lstm/info")
async def get_lstm_info():
    """
    Получение детальной информации о LSTM модели
    """
    try:
        lstm_info = dl_engine.lstm_model.get_model_info()
        return {
            "status": "success",
            "lstm_model": lstm_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения информации о LSTM: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/cnn/info")
async def get_cnn_info():
    """
    Получение детальной информации о CNN модели
    """
    try:
        cnn_info = dl_engine.cnn_model.get_model_info()
        return {
            "status": "success",
            "cnn_model": cnn_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения информации о CNN: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/initialize")
async def initialize_models():
    """
    Принудительная инициализация моделей
    """
    try:
        results = await dl_engine.initialize_models()
        return {
            "status": "success",
            "initialization_results": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка инициализации моделей: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data-source")
async def update_data_source(source_update: DataSourceUpdate):
    """
    Обновление источника рыночных данных
    """
    try:
        source_map = {
            'demo': DataSource.DEMO,
            'bingx': DataSource.BINGX,
            'binance': DataSource.BINANCE,
            'yahoo': DataSource.YAHOO
        }
        
        if source_update.source not in source_map:
            raise HTTPException(
                status_code=400,
                detail=f"Неверный источник данных. Доступные: {list(source_map.keys())}"
            )
        
        new_source = source_map[source_update.source]
        market_data_service.default_source = new_source
        market_data_service.clear_cache()  # Очищаем кэш при смене источника
        
        return {
            "status": "success",
            "message": f"Источник данных изменен на {source_update.source}",
            "new_source": source_update.source,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка обновления источника данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data-source/status")
async def get_data_source_status():
    """
    Получение информации об источнике данных
    """
    try:
        cache_info = market_data_service.get_cache_info()
        return {
            "status": "success",
            "current_source": market_data_service.default_source.value,
            "cache_info": cache_info,
            "available_sources": ["demo", "bingx", "binance", "yahoo"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса источника данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/data-source/cache")
async def clear_data_cache():
    """
    Очистка кэша рыночных данных
    """
    try:
        market_data_service.clear_cache()
        return {
            "status": "success",
            "message": "Кэш рыночных данных очищен",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка очистки кэша данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Вспомогательные функции
async def _get_sample_data(symbol: str, timeframe: str, days_back: int = None, periods: int = None) -> pd.DataFrame:
    """
    Заглушка для получения рыночных данных
    В реальной реализации здесь должен быть вызов к MarketDataService
    """
    # Генерируем синтетические данные для демонстрации
    if periods:
        size = periods
    else:
        # Примерное количество записей на основе таймфрейма и дней
        timeframe_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440
        }
        minutes_per_day = 1440
        size = (days_back * minutes_per_day) // timeframe_minutes.get(timeframe, 60)
    
    # Генерируем случайные данные, похожие на реальные
    np.random.seed(42)  # Для воспроизводимости
    
    dates = pd.date_range(end=datetime.now(), periods=size, freq='H')
    
    # Симуляция цены с трендом и волатильностью
    base_price = 50000  # Базовая цена для BTC
    price_changes = np.random.normal(0, 0.02, size)  # 2% волатильность
    prices = [base_price]
    
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    prices = np.array(prices)
    
    # Генерируем OHLCV данные
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, size))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, size))),
        'close': prices,
        'volume': np.random.uniform(100, 1000, size)
    })
    
    # Корректируем high и low
    data['high'] = np.maximum(data['high'], np.maximum(data['open'], data['close']))
    data['low'] = np.minimum(data['low'], np.minimum(data['open'], data['close']))
    
    return data 