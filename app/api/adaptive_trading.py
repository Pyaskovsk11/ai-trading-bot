from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..services.adaptive_trading_service import (
    AdaptiveTradingService, 
    AggressivenessProfile, 
    AIMode,
    TradingSignal
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/adaptive-trading", tags=["Adaptive Trading"])

# Глобальный экземпляр адаптивного торгового сервиса
adaptive_service = AdaptiveTradingService()

# Pydantic модели для API
class ProfileChangeRequest(BaseModel):
    profile: str = Field(..., description="Профиль агрессивности: conservative, moderate, aggressive")

class AIModeChangeRequest(BaseModel):
    mode: str = Field(..., description="AI-режим: manual, semi_auto, full_auto, ai_adaptive")

class MarketAnalysisRequest(BaseModel):
    symbol: str = Field(..., description="Торговая пара (например, BTC/USDT)")
    timeframe: str = Field(default="1h", description="Таймфрейм данных")
    periods: int = Field(default=100, description="Количество периодов для анализа")

class PositionSizeRequest(BaseModel):
    symbol: str = Field(..., description="Торговая пара")
    account_balance: float = Field(..., gt=0, description="Баланс аккаунта в USDT")
    current_price: float = Field(..., gt=0, description="Текущая цена")
    confidence: float = Field(..., ge=0, le=1, description="Уверенность сигнала")

class TradingSignalResponse(BaseModel):
    symbol: str
    signal: str
    confidence: float
    source: str
    timestamp: str
    metadata: Dict
    execution_recommendation: Dict

class SettingsResponse(BaseModel):
    profile: str
    ai_mode: str
    settings: Dict
    model_weights: Dict
    signals_count: int
    last_signal: Optional[Dict]

@router.post("/initialize")
async def initialize_service():
    """
    Инициализация адаптивного торгового сервиса
    """
    try:
        success = await adaptive_service.initialize()
        if success:
            return {
                "status": "success",
                "message": "Адаптивный торговый сервис инициализирован",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Ошибка инициализации сервиса")
    except Exception as e:
        logger.error(f"Ошибка инициализации: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/profile")
async def change_aggressiveness_profile(request: ProfileChangeRequest):
    """
    Изменение профиля агрессивности торговли
    """
    try:
        # Валидация профиля
        profile_map = {
            'conservative': AggressivenessProfile.CONSERVATIVE,
            'moderate': AggressivenessProfile.MODERATE,
            'aggressive': AggressivenessProfile.AGGRESSIVE
        }
        
        if request.profile not in profile_map:
            raise HTTPException(
                status_code=400,
                detail=f"Неверный профиль. Доступные: {list(profile_map.keys())}"
            )
        
        profile = profile_map[request.profile]
        adaptive_service.set_aggressiveness_profile(profile)
        
        return {
            "status": "success",
            "message": f"Профиль агрессивности изменен на {request.profile}",
            "new_profile": request.profile,
            "settings": adaptive_service.profiles[profile],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка изменения профиля: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-mode")
async def change_ai_mode(request: AIModeChangeRequest):
    """
    Изменение AI-режима торговли
    """
    try:
        # Валидация режима
        mode_map = {
            'manual': AIMode.MANUAL,
            'semi_auto': AIMode.SEMI_AUTO,
            'full_auto': AIMode.FULL_AUTO,
            'ai_adaptive': AIMode.AI_ADAPTIVE
        }
        
        if request.mode not in mode_map:
            raise HTTPException(
                status_code=400,
                detail=f"Неверный AI-режим. Доступные: {list(mode_map.keys())}"
            )
        
        mode = mode_map[request.mode]
        adaptive_service.set_ai_mode(mode)
        
        return {
            "status": "success",
            "message": f"AI-режим изменен на {request.mode}",
            "new_mode": request.mode,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка изменения AI-режима: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=TradingSignalResponse)
async def analyze_market(request: MarketAnalysisRequest):
    """
    Анализ рынка и генерация торгового сигнала
    """
    try:
        # Получаем торговый сигнал
        signal = await adaptive_service.analyze_market(
            symbol=request.symbol,
            timeframe=request.timeframe,
            periods=request.periods
        )
        
        # Проверяем, следует ли выполнить торговлю
        should_execute, execution_reason = await adaptive_service.should_execute_trade(signal)
        
        return TradingSignalResponse(
            symbol=signal.symbol,
            signal=signal.signal,
            confidence=signal.confidence,
            source=signal.source,
            timestamp=signal.timestamp.isoformat(),
            metadata=signal.metadata,
            execution_recommendation={
                "should_execute": should_execute,
                "reason": execution_reason,
                "current_profile": adaptive_service.current_profile.value,
                "current_ai_mode": adaptive_service.current_ai_mode.value
            }
        )
        
    except Exception as e:
        logger.error(f"Ошибка анализа рынка: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/position-size")
async def calculate_position_size(request: PositionSizeRequest):
    """
    Расчет размера позиции на основе профиля агрессивности и уверенности AI
    """
    try:
        # Создаем временный сигнал для расчета
        temp_signal = TradingSignal(
            symbol=request.symbol,
            signal='buy',  # Не важно для расчета размера
            confidence=request.confidence,
            source='api',
            timestamp=datetime.now()
        )
        
        position_quantity = await adaptive_service.calculate_position_size(
            signal=temp_signal,
            account_balance=request.account_balance,
            current_price=request.current_price
        )
        
        # Дополнительные расчеты
        profile_config = adaptive_service.profiles[adaptive_service.current_profile]
        base_risk = profile_config['risk_per_trade']
        multiplier = profile_config['position_size_multiplier']
        adjusted_risk = base_risk * multiplier * request.confidence
        position_value = position_quantity * request.current_price
        
        return {
            "status": "success",
            "symbol": request.symbol,
            "position_quantity": round(position_quantity, 8),
            "position_value_usdt": round(position_value, 2),
            "risk_percentage": round(adjusted_risk * 100, 3),
            "confidence": request.confidence,
            "current_profile": adaptive_service.current_profile.value,
            "calculation_details": {
                "base_risk": base_risk,
                "profile_multiplier": multiplier,
                "confidence_multiplier": request.confidence,
                "final_risk": adjusted_risk,
                "account_balance": request.account_balance,
                "current_price": request.current_price
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка расчета размера позиции: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings", response_model=SettingsResponse)
async def get_current_settings():
    """
    Получение текущих настроек адаптивной торговли
    """
    try:
        settings = adaptive_service.get_current_settings()
        return SettingsResponse(**settings)
    except Exception as e:
        logger.error(f"Ошибка получения настроек: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_performance_metrics():
    """
    Получение метрик производительности адаптивной торговли
    """
    try:
        metrics = adaptive_service.get_performance_metrics()
        return {
            "status": "success",
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения метрик: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signal-history")
async def get_signal_history(limit: int = 50):
    """
    Получение истории торговых сигналов
    """
    try:
        if limit > 500:
            limit = 500  # Ограничиваем максимальное количество
        
        signals = adaptive_service.signal_history[-limit:] if adaptive_service.signal_history else []
        
        # Конвертируем в словари для JSON
        signal_dicts = []
        for signal in signals:
            signal_dict = {
                'symbol': signal.symbol,
                'signal': signal.signal,
                'confidence': signal.confidence,
                'source': signal.source,
                'timestamp': signal.timestamp.isoformat(),
                'metadata': signal.metadata
            }
            signal_dicts.append(signal_dict)
        
        return {
            "status": "success",
            "signals": signal_dicts,
            "total_count": len(adaptive_service.signal_history),
            "returned_count": len(signal_dicts),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения истории сигналов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profiles")
async def get_available_profiles():
    """
    Получение списка доступных профилей агрессивности
    """
    try:
        profiles_info = {}
        for profile, config in adaptive_service.profiles.items():
            profiles_info[profile.value] = {
                "name": profile.value,
                "description": f"Риск: {config['risk_per_trade']*100}%, "
                             f"Стоп: {config['stop_loss_atr']} ATR, "
                             f"Порог: {config['confidence_threshold']*100}%",
                "settings": config
            }
        
        return {
            "status": "success",
            "profiles": profiles_info,
            "current_profile": adaptive_service.current_profile.value,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения профилей: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-modes")
async def get_available_ai_modes():
    """
    Получение списка доступных AI-режимов
    """
    try:
        modes_info = {
            "manual": {
                "name": "Ручной",
                "description": "Только ручные сигналы, автоматическая торговля отключена"
            },
            "semi_auto": {
                "name": "Полуавтоматический", 
                "description": "AI генерирует сигналы, требуется подтверждение пользователя"
            },
            "full_auto": {
                "name": "Автоматический",
                "description": "Автоматическая торговля по AI сигналам"
            },
            "ai_adaptive": {
                "name": "AI-адаптивный",
                "description": "Полная автономность с машинным обучением"
            }
        }
        
        return {
            "status": "success",
            "ai_modes": modes_info,
            "current_mode": adaptive_service.current_ai_mode.value,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения AI-режимов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/signal-history")
async def clear_signal_history():
    """
    Очистка истории торговых сигналов
    """
    try:
        count = len(adaptive_service.signal_history)
        adaptive_service.signal_history.clear()
        
        return {
            "status": "success",
            "message": f"История сигналов очищена ({count} записей удалено)",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка очистки истории: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 