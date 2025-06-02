"""
API endpoints for BacktestEngine
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging
import asyncio

from app.services.backtest_engine import (
    backtest_engine, 
    BacktestConfig, 
    BacktestMetrics,
    BacktestTrade
)
from app.services.trading_strategy_manager import StrategyConfig, StrategyType
from app.services.adaptive_trading_service import AggressivenessProfile, AIMode

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backtest", tags=["Backtest"])

# Pydantic models for API
class BacktestRequest(BaseModel):
    symbols: List[str] = Field(..., description="Список торговых пар")
    start_date: str = Field(..., description="Дата начала (YYYY-MM-DD)")
    end_date: str = Field(..., description="Дата окончания (YYYY-MM-DD)")
    timeframe: str = Field(default="1h", description="Таймфрейм")
    
    # Конфигурация стратегии
    strategy_type: str = Field(default="adaptive", description="Тип стратегии")
    aggressiveness: str = Field(default="moderate", description="Профиль агрессивности")
    ai_mode: str = Field(default="semi_auto", description="AI режим")
    ensemble_weights: Optional[Dict[str, float]] = None
    
    # Конфигурация бэктеста
    initial_capital: float = Field(default=100000.0, description="Начальный капитал")
    commission_rate: float = Field(default=0.001, description="Комиссия")
    slippage_rate: float = Field(default=0.0005, description="Проскальзывание")
    position_size: float = Field(default=0.02, description="Размер позиции (% от капитала)")
    max_positions: int = Field(default=10, description="Максимум позиций")
    use_stop_loss: bool = Field(default=True, description="Использовать стоп-лосс")
    max_trade_duration: int = Field(default=24, description="Максимальная длительность сделки (часы)")

class BacktestResponse(BaseModel):
    status: str
    backtest_id: str
    message: str
    estimated_duration: int  # секунды

class BacktestResultResponse(BaseModel):
    status: str
    config: Dict
    strategy_config: Dict
    period: Dict
    symbols: List[str]
    metrics: Dict
    trades_count: int
    summary: Dict

class QuickBacktestRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT", description="Торговая пара")
    days: int = Field(default=30, description="Количество дней")
    strategy_type: str = Field(default="adaptive", description="Тип стратегии")

# Хранилище активных бэктестов
active_backtests: Dict[str, Dict] = {}

@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """
    Запуск полного бэктеста
    """
    try:
        # Валидация дат
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)
        
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="Дата начала должна быть раньше даты окончания")
        
        if (end_date - start_date).days > 365:
            raise HTTPException(status_code=400, detail="Максимальный период бэктеста: 365 дней")
        
        # Валидация символов
        if len(request.symbols) > 20:
            raise HTTPException(status_code=400, detail="Максимум 20 символов")
        
        # Создание конфигураций
        strategy_config = StrategyConfig(
            strategy_type=StrategyType(request.strategy_type),
            aggressiveness=AggressivenessProfile(request.aggressiveness),
            ai_mode=AIMode(request.ai_mode),
            ensemble_weights=request.ensemble_weights
        )
        
        backtest_config = BacktestConfig(
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate,
            slippage_rate=request.slippage_rate,
            position_size=request.position_size,
            max_positions=request.max_positions,
            use_stop_loss=request.use_stop_loss,
            max_trade_duration=request.max_trade_duration
        )
        
        # Генерация ID бэктеста
        backtest_id = f"bt_{int(datetime.now().timestamp())}"
        
        # Оценка времени выполнения
        estimated_duration = len(request.symbols) * (end_date - start_date).days * 2  # секунды
        
        # Сохранение в активные бэктесты
        active_backtests[backtest_id] = {
            'status': 'running',
            'start_time': datetime.now(),
            'estimated_duration': estimated_duration,
            'progress': 0,
            'result': None
        }
        
        # Запуск в фоне
        background_tasks.add_task(
            _run_backtest_background,
            backtest_id,
            strategy_config,
            request.symbols,
            start_date,
            end_date,
            request.timeframe,
            backtest_config
        )
        
        logger.info(f"Запущен бэктест {backtest_id}: {len(request.symbols)} символов, "
                   f"{(end_date - start_date).days} дней")
        
        return BacktestResponse(
            status="started",
            backtest_id=backtest_id,
            message=f"Бэктест запущен для {len(request.symbols)} символов",
            estimated_duration=estimated_duration
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Неверные параметры: {e}")
    except Exception as e:
        logger.error(f"Ошибка запуска бэктеста: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _run_backtest_background(backtest_id: str,
                                 strategy_config: StrategyConfig,
                                 symbols: List[str],
                                 start_date: datetime,
                                 end_date: datetime,
                                 timeframe: str,
                                 backtest_config: BacktestConfig):
    """Выполнение бэктеста в фоновом режиме"""
    try:
        # Создаем новый экземпляр для этого бэктеста
        from app.services.backtest_engine import BacktestEngine
        engine = BacktestEngine(backtest_config)
        
        # Обновляем прогресс
        active_backtests[backtest_id]['progress'] = 10
        
        # Запускаем бэктест
        result = await engine.run_backtest(
            strategy_config, symbols, start_date, end_date, timeframe
        )
        
        # Сохраняем результат
        active_backtests[backtest_id].update({
            'status': 'completed',
            'progress': 100,
            'result': result,
            'end_time': datetime.now()
        })
        
        logger.info(f"Бэктест {backtest_id} завершен успешно")
        
    except Exception as e:
        logger.error(f"Ошибка выполнения бэктеста {backtest_id}: {e}")
        active_backtests[backtest_id].update({
            'status': 'error',
            'error': str(e),
            'end_time': datetime.now()
        })

@router.get("/status/{backtest_id}")
async def get_backtest_status(backtest_id: str):
    """
    Получение статуса бэктеста
    """
    if backtest_id not in active_backtests:
        raise HTTPException(status_code=404, detail="Бэктест не найден")
    
    backtest_info = active_backtests[backtest_id]
    
    response = {
        'backtest_id': backtest_id,
        'status': backtest_info['status'],
        'progress': backtest_info['progress'],
        'start_time': backtest_info['start_time'].isoformat()
    }
    
    if 'end_time' in backtest_info:
        response['end_time'] = backtest_info['end_time'].isoformat()
        duration = (backtest_info['end_time'] - backtest_info['start_time']).total_seconds()
        response['duration_seconds'] = duration
    
    if 'error' in backtest_info:
        response['error'] = backtest_info['error']
    
    return response

@router.get("/result/{backtest_id}", response_model=BacktestResultResponse)
async def get_backtest_result(backtest_id: str):
    """
    Получение результатов бэктеста
    """
    if backtest_id not in active_backtests:
        raise HTTPException(status_code=404, detail="Бэктест не найден")
    
    backtest_info = active_backtests[backtest_id]
    
    if backtest_info['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Бэктест не завершен. Статус: {backtest_info['status']}")
    
    result = backtest_info['result']
    
    return BacktestResultResponse(
        status="success",
        config=result['config'],
        strategy_config=result['strategy_config'],
        period=result['period'],
        symbols=result['symbols'],
        metrics=result['metrics'],
        trades_count=len(result['trades']),
        summary=result['summary']
    )

@router.get("/result/{backtest_id}/trades")
async def get_backtest_trades(backtest_id: str, limit: int = 100, offset: int = 0):
    """
    Получение сделок бэктеста
    """
    if backtest_id not in active_backtests:
        raise HTTPException(status_code=404, detail="Бэктест не найден")
    
    backtest_info = active_backtests[backtest_id]
    
    if backtest_info['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Бэктест не завершен")
    
    trades = backtest_info['result']['trades']
    
    # Пагинация
    start_idx = offset
    end_idx = min(offset + limit, len(trades))
    
    return {
        'trades': trades[start_idx:end_idx],
        'total_trades': len(trades),
        'offset': offset,
        'limit': limit,
        'has_more': end_idx < len(trades)
    }

@router.get("/result/{backtest_id}/equity")
async def get_backtest_equity_curve(backtest_id: str):
    """
    Получение кривой капитала
    """
    if backtest_id not in active_backtests:
        raise HTTPException(status_code=404, detail="Бэктест не найден")
    
    backtest_info = active_backtests[backtest_id]
    
    if backtest_info['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Бэктест не завершен")
    
    return {
        'equity_curve': backtest_info['result']['equity_curve'],
        'total_points': len(backtest_info['result']['equity_curve'])
    }

@router.post("/quick", response_model=Dict)
async def run_quick_backtest(request: QuickBacktestRequest):
    """
    Быстрый бэктест для одного символа
    """
    try:
        # Создание дат
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.days)
        
        # Конфигурация стратегии
        strategy_config = StrategyConfig(
            strategy_type=StrategyType(request.strategy_type),
            aggressiveness=AggressivenessProfile.MODERATE,
            ai_mode=AIMode.SEMI_AUTO
        )
        
        # Базовая конфигурация бэктеста
        backtest_config = BacktestConfig(
            initial_capital=10000.0,
            position_size=0.1  # 10% для быстрого теста
        )
        
        # Создаем экземпляр движка
        from app.services.backtest_engine import BacktestEngine
        engine = BacktestEngine(backtest_config)
        
        # Запускаем бэктест
        result = await engine.run_backtest(
            strategy_config, [request.symbol], start_date, end_date, "1h"
        )
        
        # Возвращаем упрощенный результат
        metrics = result['metrics']
        
        return {
            'symbol': request.symbol,
            'period_days': request.days,
            'strategy_type': request.strategy_type,
            'performance': {
                'total_return_pct': round(metrics['total_return_pct'], 2),
                'total_trades': metrics['total_trades'],
                'win_rate': round(metrics['win_rate'] * 100, 1),
                'sharpe_ratio': round(metrics['sharpe_ratio'], 2),
                'max_drawdown_pct': round(metrics['max_drawdown_pct'], 2),
                'profit_factor': round(metrics['profit_factor'], 2)
            },
            'summary': result['summary'],
            'recent_trades': result['trades'][-5:] if result['trades'] else []
        }
        
    except Exception as e:
        logger.error(f"Ошибка быстрого бэктеста: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active")
async def get_active_backtests():
    """
    Получение списка активных бэктестов
    """
    result = []
    
    for backtest_id, info in active_backtests.items():
        result.append({
            'backtest_id': backtest_id,
            'status': info['status'],
            'progress': info['progress'],
            'start_time': info['start_time'].isoformat(),
            'estimated_duration': info.get('estimated_duration', 0)
        })
    
    return {
        'active_backtests': result,
        'total_count': len(result)
    }

@router.delete("/cancel/{backtest_id}")
async def cancel_backtest(backtest_id: str):
    """
    Отмена бэктеста
    """
    if backtest_id not in active_backtests:
        raise HTTPException(status_code=404, detail="Бэктест не найден")
    
    backtest_info = active_backtests[backtest_id]
    
    if backtest_info['status'] in ['completed', 'error']:
        raise HTTPException(status_code=400, detail="Бэктест уже завершен")
    
    # Помечаем как отмененный
    active_backtests[backtest_id].update({
        'status': 'cancelled',
        'end_time': datetime.now()
    })
    
    return {
        'status': 'success',
        'message': f'Бэктест {backtest_id} отменен'
    }

@router.delete("/cleanup")
async def cleanup_old_backtests():
    """
    Очистка старых бэктестов (старше 24 часов)
    """
    cutoff_time = datetime.now() - timedelta(hours=24)
    removed_count = 0
    
    for backtest_id in list(active_backtests.keys()):
        backtest_info = active_backtests[backtest_id]
        
        # Проверяем время создания
        if backtest_info['start_time'] < cutoff_time:
            del active_backtests[backtest_id]
            removed_count += 1
    
    return {
        'status': 'success',
        'message': f'Удалено {removed_count} старых бэктестов',
        'remaining_count': len(active_backtests)
    }

@router.get("/strategies/performance")
async def compare_strategies_performance():
    """
    Сравнение производительности различных стратегий
    """
    try:
        # Быстрое сравнение стратегий на BTCUSDT за последние 30 дней
        symbol = "BTCUSDT"
        days = 30
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        strategies = [
            ("adaptive_conservative", StrategyType.ADAPTIVE, AggressivenessProfile.CONSERVATIVE),
            ("adaptive_moderate", StrategyType.ADAPTIVE, AggressivenessProfile.MODERATE),
            ("adaptive_aggressive", StrategyType.ADAPTIVE, AggressivenessProfile.AGGRESSIVE),
            ("ml_only", StrategyType.ML_ONLY, AggressivenessProfile.MODERATE),
            ("ensemble", StrategyType.ENSEMBLE, AggressivenessProfile.MODERATE)
        ]
        
        results = []
        
        for name, strategy_type, aggressiveness in strategies:
            try:
                strategy_config = StrategyConfig(
                    strategy_type=strategy_type,
                    aggressiveness=aggressiveness,
                    ai_mode=AIMode.SEMI_AUTO
                )
                
                backtest_config = BacktestConfig(initial_capital=10000.0, position_size=0.05)
                
                from app.services.backtest_engine import BacktestEngine
                engine = BacktestEngine(backtest_config)
                
                result = await engine.run_backtest(
                    strategy_config, [symbol], start_date, end_date, "1h"
                )
                
                metrics = result['metrics']
                
                results.append({
                    'strategy_name': name,
                    'total_return_pct': round(metrics['total_return_pct'], 2),
                    'sharpe_ratio': round(metrics['sharpe_ratio'], 2),
                    'max_drawdown_pct': round(metrics['max_drawdown_pct'], 2),
                    'win_rate': round(metrics['win_rate'] * 100, 1),
                    'total_trades': metrics['total_trades'],
                    'profit_factor': round(metrics['profit_factor'], 2)
                })
                
            except Exception as e:
                logger.error(f"Ошибка тестирования стратегии {name}: {e}")
                results.append({
                    'strategy_name': name,
                    'error': str(e)
                })
        
        # Сортируем по Sharpe ratio
        valid_results = [r for r in results if 'error' not in r]
        valid_results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        
        return {
            'symbol': symbol,
            'period_days': days,
            'strategies_tested': len(strategies),
            'results': results,
            'best_strategy': valid_results[0] if valid_results else None,
            'comparison_date': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка сравнения стратегий: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 