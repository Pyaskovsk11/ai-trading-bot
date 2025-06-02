"""
API endpoints for unified trading strategy management
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.services.trading_strategy_manager import (
    strategy_manager, 
    StrategyType, 
    StrategyConfig, 
    UnifiedTradingSignal
)
from app.services.adaptive_trading_service import AggressivenessProfile, AIMode

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/strategy", tags=["Trading Strategy"])

# Pydantic models for API
class StrategyConfigRequest(BaseModel):
    strategy_type: str = "adaptive"
    aggressiveness: str = "moderate"
    ai_mode: str = "semi_auto"
    ensemble_weights: Optional[Dict[str, float]] = None

class SignalRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"

class SignalResponse(BaseModel):
    symbol: str
    signal: str
    confidence: float
    strategy_type: str
    timestamp: datetime
    should_execute: bool
    position_size: float
    stop_loss: float
    execution_reason: str
    metadata: Dict
    risk_metrics: Dict

class PerformanceResponse(BaseModel):
    total_signals: int
    recent_signals_24h: int
    buy_signals_24h: int
    sell_signals_24h: int
    hold_signals_24h: int
    avg_confidence_24h: float
    current_strategy: str
    current_profile: str
    current_ai_mode: str
    strategy_performance: Dict

@router.on_event("startup")
async def initialize_strategy_manager():
    """Инициализация менеджера стратегий при запуске"""
    try:
        success = await strategy_manager.initialize()
        if success:
            logger.info("✅ TradingStrategyManager успешно инициализирован")
        else:
            logger.error("❌ Ошибка инициализации TradingStrategyManager")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка инициализации: {e}")

@router.get("/config", response_model=Dict)
async def get_current_config():
    """
    Получить текущую конфигурацию стратегии
    """
    try:
        config = strategy_manager.get_current_config()
        return {
            "status": "success",
            "data": config
        }
    except Exception as e:
        logger.error(f"Ошибка получения конфигурации: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config")
async def set_strategy_config(config_request: StrategyConfigRequest):
    """
    Установить конфигурацию стратегии
    """
    try:
        # Валидация и конвертация параметров
        strategy_type = StrategyType(config_request.strategy_type)
        aggressiveness = AggressivenessProfile(config_request.aggressiveness)
        ai_mode = AIMode(config_request.ai_mode)
        
        # Создание конфигурации
        config = StrategyConfig(
            strategy_type=strategy_type,
            aggressiveness=aggressiveness,
            ai_mode=ai_mode,
            ensemble_weights=config_request.ensemble_weights
        )
        
        # Применение конфигурации
        strategy_manager.set_strategy_config(config)
        
        return {
            "status": "success",
            "message": f"Конфигурация установлена: {strategy_type.value}",
            "data": strategy_manager.get_current_config()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Неверные параметры: {e}")
    except Exception as e:
        logger.error(f"Ошибка установки конфигурации: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signal", response_model=SignalResponse)
async def get_trading_signal(signal_request: SignalRequest):
    """
    Получить торговый сигнал для указанного символа
    """
    try:
        # Получаем унифицированный сигнал
        signal = await strategy_manager.get_unified_signal(
            symbol=signal_request.symbol,
            timeframe=signal_request.timeframe
        )
        
        # Добавляем в историю
        strategy_manager.add_signal_to_history(signal)
        
        # Конвертируем в response модель
        response = SignalResponse(
            symbol=signal.symbol,
            signal=signal.signal,
            confidence=signal.confidence,
            strategy_type=signal.strategy_type,
            timestamp=signal.timestamp,
            should_execute=signal.should_execute,
            position_size=signal.position_size,
            stop_loss=signal.stop_loss,
            execution_reason=signal.execution_reason,
            metadata=signal.metadata,
            risk_metrics=signal.risk_metrics
        )
        
        logger.info(f"Сигнал для {signal_request.symbol}: {signal.signal} "
                   f"(уверенность: {signal.confidence:.2f}, "
                   f"стратегия: {signal.strategy_type})")
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка получения сигнала для {signal_request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signals/batch")
async def get_batch_signals(symbols: str, timeframe: str = "1h"):
    """
    Получить сигналы для нескольких символов
    symbols: строка с символами через запятую (например: "BTCUSDT,ETHUSDT,ADAUSDT")
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        
        if len(symbol_list) > 10:
            raise HTTPException(status_code=400, detail="Максимум 10 символов за раз")
        
        results = []
        
        for symbol in symbol_list:
            try:
                signal = await strategy_manager.get_unified_signal(symbol, timeframe)
                strategy_manager.add_signal_to_history(signal)
                
                results.append({
                    "symbol": signal.symbol,
                    "signal": signal.signal,
                    "confidence": signal.confidence,
                    "strategy_type": signal.strategy_type,
                    "should_execute": signal.should_execute,
                    "execution_reason": signal.execution_reason,
                    "timestamp": signal.timestamp.isoformat()
                })
                
            except Exception as e:
                logger.error(f"Ошибка сигнала для {symbol}: {e}")
                results.append({
                    "symbol": symbol,
                    "signal": "error",
                    "confidence": 0.0,
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "timeframe": timeframe,
            "signals": results,
            "total_processed": len(symbol_list)
        }
        
    except Exception as e:
        logger.error(f"Ошибка batch обработки: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance", response_model=PerformanceResponse)
async def get_performance_metrics():
    """
    Получить метрики производительности стратегий
    """
    try:
        metrics = strategy_manager.get_performance_metrics()
        
        return PerformanceResponse(
            total_signals=metrics.get('total_signals', 0),
            recent_signals_24h=metrics.get('recent_signals_24h', 0),
            buy_signals_24h=metrics.get('buy_signals_24h', 0),
            sell_signals_24h=metrics.get('sell_signals_24h', 0),
            hold_signals_24h=metrics.get('hold_signals_24h', 0),
            avg_confidence_24h=metrics.get('avg_confidence_24h', 0.0),
            current_strategy=metrics.get('current_strategy', 'unknown'),
            current_profile=metrics.get('current_profile', 'unknown'),
            current_ai_mode=metrics.get('current_ai_mode', 'unknown'),
            strategy_performance=metrics.get('strategy_performance', {})
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения метрик: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_signal_history(limit: int = 50, strategy_type: Optional[str] = None):
    """
    Получить историю сигналов
    """
    try:
        history = strategy_manager.signal_history
        
        # Фильтрация по типу стратегии
        if strategy_type:
            history = [s for s in history if s.strategy_type == strategy_type]
        
        # Ограничение количества
        history = history[-limit:] if len(history) > limit else history
        
        # Конвертация в JSON-совместимый формат
        result = []
        for signal in history:
            result.append({
                "symbol": signal.symbol,
                "signal": signal.signal,
                "confidence": signal.confidence,
                "strategy_type": signal.strategy_type,
                "timestamp": signal.timestamp.isoformat(),
                "should_execute": signal.should_execute,
                "execution_reason": signal.execution_reason,
                "metadata": signal.metadata
            })
        
        return {
            "status": "success",
            "total_history": len(strategy_manager.signal_history),
            "returned": len(result),
            "filter": strategy_type,
            "signals": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения истории: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies/available")
async def get_available_strategies():
    """
    Получить список доступных стратегий и их параметров
    """
    return {
        "status": "success",
        "data": {
            "strategy_types": [
                {
                    "value": "adaptive",
                    "name": "Адаптивная стратегия",
                    "description": "Рекомендуемая стратегия с 3 профилями агрессивности",
                    "recommended": True
                },
                {
                    "value": "ml_only",
                    "name": "Только Machine Learning",
                    "description": "LSTM + CNN ансамбль для предсказаний"
                },
                {
                    "value": "basic",
                    "name": "Базовая стратегия",
                    "description": "Простая техническая аналитика + новости"
                },
                {
                    "value": "ensemble",
                    "name": "Комбинированная стратегия",
                    "description": "Объединение всех подходов с весами"
                }
            ],
            "aggressiveness_profiles": [
                {
                    "value": "conservative",
                    "name": "Консервативный",
                    "risk_per_trade": "1%",
                    "confidence_threshold": "80%",
                    "description": "Максимальная защита капитала"
                },
                {
                    "value": "moderate",
                    "name": "Умеренный",
                    "risk_per_trade": "2%",
                    "confidence_threshold": "65%",
                    "description": "Баланс риска и доходности",
                    "recommended": True
                },
                {
                    "value": "aggressive",
                    "name": "Агрессивный",
                    "risk_per_trade": "5%",
                    "confidence_threshold": "55%",
                    "description": "Максимальная доходность"
                }
            ],
            "ai_modes": [
                {
                    "value": "manual",
                    "name": "Ручной",
                    "description": "Только рекомендации AI"
                },
                {
                    "value": "semi_auto",
                    "name": "Полуавтоматический",
                    "description": "AI сигналы + подтверждение пользователя",
                    "recommended": True
                },
                {
                    "value": "full_auto",
                    "name": "Полностью автоматический",
                    "description": "Автоматическое выполнение сигналов"
                },
                {
                    "value": "ai_adaptive",
                    "name": "AI-адаптивный",
                    "description": "Полная автономность с самообучением"
                }
            ]
        }
    }

@router.post("/test")
async def test_strategy_manager():
    """
    Тестирование работы менеджера стратегий
    """
    try:
        # Тест различных стратегий
        test_symbol = "BTCUSDT"
        results = {}
        
        # Тест адаптивной стратегии
        config = StrategyConfig(strategy_type=StrategyType.ADAPTIVE)
        strategy_manager.set_strategy_config(config)
        adaptive_signal = await strategy_manager.get_unified_signal(test_symbol)
        results['adaptive'] = {
            'signal': adaptive_signal.signal,
            'confidence': adaptive_signal.confidence,
            'should_execute': adaptive_signal.should_execute
        }
        
        # Тест ML стратегии
        config = StrategyConfig(strategy_type=StrategyType.ML_ONLY)
        strategy_manager.set_strategy_config(config)
        ml_signal = await strategy_manager.get_unified_signal(test_symbol)
        results['ml_only'] = {
            'signal': ml_signal.signal,
            'confidence': ml_signal.confidence,
            'should_execute': ml_signal.should_execute
        }
        
        # Тест ensemble стратегии
        config = StrategyConfig(strategy_type=StrategyType.ENSEMBLE)
        strategy_manager.set_strategy_config(config)
        ensemble_signal = await strategy_manager.get_unified_signal(test_symbol)
        results['ensemble'] = {
            'signal': ensemble_signal.signal,
            'confidence': ensemble_signal.confidence,
            'should_execute': ensemble_signal.should_execute
        }
        
        return {
            "status": "success",
            "message": "Тестирование завершено успешно",
            "test_symbol": test_symbol,
            "results": results,
            "performance": strategy_manager.get_performance_metrics()
        }
        
    except Exception as e:
        logger.error(f"Ошибка тестирования: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 