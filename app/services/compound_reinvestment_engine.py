"""
Compound Reinvestment Engine - Система составного реинвестирования для экспоненциального роста
ЦЕЛЬ: Автоматическое реинвестирование прибыли для достижения 100% доходности
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import json

logger = logging.getLogger(__name__)

class CompoundingMode(Enum):
    """Режимы составного реинвестирования"""
    CONSERVATIVE = "conservative"  # 50% прибыли реинвестируется
    MODERATE = "moderate"         # 75% прибыли реинвестируется
    AGGRESSIVE = "aggressive"     # 90% прибыли реинвестируется
    EXTREME = "extreme"           # 100% прибыли реинвестируется

@dataclass
class CompoundingConfig:
    """Конфигурация составного реинвестирования"""
    mode: CompoundingMode
    reinvestment_percentage: float  # Процент прибыли для реинвестирования
    min_profit_threshold: float     # Минимальная прибыль для реинвестирования
    max_position_size: float        # Максимальный размер позиции
    profit_taking_levels: List[float]  # Уровни фиксации прибыли
    risk_scaling_factor: float      # Коэффициент масштабирования риска
    compound_frequency: str         # Частота реинвестирования

class CompoundReinvestmentEngine:
    """
    Система составного реинвестирования для экспоненциального роста капитала
    """
    
    def __init__(self, mode: CompoundingMode = CompoundingMode.MODERATE):
        self.mode = mode
        self.config = self._get_compounding_config()
        self.initial_capital = 0.0
        self.current_capital = 0.0
        self.total_profit = 0.0
        self.reinvested_amount = 0.0
        self.compound_history = []
        self.position_history = []
        
        logger.info(f"Compound Reinvestment Engine инициализирован в режиме {mode.value}")
    
    def _get_compounding_config(self) -> CompoundingConfig:
        """Получение конфигурации для режима реинвестирования"""
        configs = {
            CompoundingMode.CONSERVATIVE: CompoundingConfig(
                mode=CompoundingMode.CONSERVATIVE,
                reinvestment_percentage=0.50,  # 50% прибыли
                min_profit_threshold=0.02,     # 2% минимум
                max_position_size=0.30,        # 30% максимум
                profit_taking_levels=[0.10, 0.25, 0.50],  # 10%, 25%, 50%
                risk_scaling_factor=0.8,       # Консервативное масштабирование
                compound_frequency="daily"
            ),
            CompoundingMode.MODERATE: CompoundingConfig(
                mode=CompoundingMode.MODERATE,
                reinvestment_percentage=0.75,  # 75% прибыли
                min_profit_threshold=0.015,    # 1.5% минимум
                max_position_size=0.50,        # 50% максимум
                profit_taking_levels=[0.15, 0.35, 0.75],  # 15%, 35%, 75%
                risk_scaling_factor=1.0,       # Нормальное масштабирование
                compound_frequency="trade"
            ),
            CompoundingMode.AGGRESSIVE: CompoundingConfig(
                mode=CompoundingMode.AGGRESSIVE,
                reinvestment_percentage=0.90,  # 90% прибыли
                min_profit_threshold=0.01,     # 1% минимум
                max_position_size=0.70,        # 70% максимум
                profit_taking_levels=[0.20, 0.50, 1.00],  # 20%, 50%, 100%
                risk_scaling_factor=1.2,       # Агрессивное масштабирование
                compound_frequency="immediate"
            ),
            CompoundingMode.EXTREME: CompoundingConfig(
                mode=CompoundingMode.EXTREME,
                reinvestment_percentage=1.00,  # 100% прибыли
                min_profit_threshold=0.005,    # 0.5% минимум
                max_position_size=0.90,        # 90% максимум
                profit_taking_levels=[0.25, 0.75, 1.50],  # 25%, 75%, 150%
                risk_scaling_factor=1.5,       # Экстремальное масштабирование
                compound_frequency="immediate"
            )
        }
        return configs[self.mode]
    
    def initialize_capital(self, initial_amount: float):
        """Инициализация начального капитала"""
        self.initial_capital = initial_amount
        self.current_capital = initial_amount
        self.total_profit = 0.0
        self.reinvested_amount = 0.0
        self.compound_history = []
        self.position_history = []
        
        logger.info(f"Капитал инициализирован: ${initial_amount:,.2f}")
    
    def calculate_position_size(self, signal_confidence: float, market_volatility: float = 0.02) -> float:
        """Расчет размера позиции с учетом составного роста"""
        try:
            # Базовый размер позиции на основе уверенности
            base_size = min(signal_confidence * 0.5, self.config.max_position_size)
            
            # Коэффициент роста капитала
            growth_factor = self.current_capital / self.initial_capital if self.initial_capital > 0 else 1.0
            
            # Масштабирование на основе роста (но с ограничениями)
            growth_multiplier = min(1.0 + np.log(growth_factor) * 0.2, 2.0)  # Максимум 2x
            
            # Корректировка на волатильность
            volatility_adjustment = max(0.5, 1.0 - market_volatility * 5)
            
            # Финальный размер позиции
            position_size = base_size * growth_multiplier * volatility_adjustment * self.config.risk_scaling_factor
            
            # Ограничения безопасности
            position_size = max(0.01, min(position_size, self.config.max_position_size))
            
            logger.debug(f"Размер позиции: {position_size:.3f} (рост: {growth_factor:.2f}x, уверенность: {signal_confidence:.3f})")
            
            return position_size
            
        except Exception as e:
            logger.error(f"Ошибка расчета размера позиции: {e}")
            return 0.05  # Дефолтный размер 5%
    
    def process_trade_result(self, trade_result: Dict) -> Dict:
        """Обработка результата сделки и реинвестирование"""
        try:
            profit_loss = trade_result.get('profit_loss', 0.0)
            trade_return_pct = trade_result.get('return_pct', 0.0)
            
            # Обновляем текущий капитал
            old_capital = self.current_capital
            self.current_capital += profit_loss
            
            # Если сделка прибыльная и превышает минимальный порог
            if profit_loss > 0 and trade_return_pct >= self.config.min_profit_threshold:
                
                # Рассчитываем сумму для реинвестирования
                reinvestment_amount = profit_loss * self.config.reinvestment_percentage
                
                # Обновляем статистику
                self.total_profit += profit_loss
                self.reinvested_amount += reinvestment_amount
                
                # Записываем в историю
                compound_record = {
                    'timestamp': datetime.now(),
                    'trade_profit': profit_loss,
                    'reinvestment_amount': reinvestment_amount,
                    'old_capital': old_capital,
                    'new_capital': self.current_capital,
                    'growth_factor': self.current_capital / self.initial_capital,
                    'total_return_pct': (self.current_capital - self.initial_capital) / self.initial_capital * 100,
                    'compound_effect': reinvestment_amount / self.initial_capital * 100
                }
                
                self.compound_history.append(compound_record)
                
                logger.info(f"💰 Реинвестирование: ${reinvestment_amount:,.2f} ({self.config.reinvestment_percentage:.0%} от ${profit_loss:,.2f})")
                logger.info(f"📈 Капитал: ${old_capital:,.2f} → ${self.current_capital:,.2f} ({compound_record['total_return_pct']:.2f}%)")
                
                return {
                    'reinvested': True,
                    'reinvestment_amount': reinvestment_amount,
                    'new_capital': self.current_capital,
                    'growth_factor': compound_record['growth_factor'],
                    'total_return_pct': compound_record['total_return_pct'],
                    'compound_effect': compound_record['compound_effect']
                }
            
            else:
                # Убыточная сделка или недостаточная прибыль
                logger.debug(f"Реинвестирование пропущено: прибыль ${profit_loss:.2f}, порог {self.config.min_profit_threshold:.1%}")
                
                return {
                    'reinvested': False,
                    'reason': 'Недостаточная прибыль' if profit_loss > 0 else 'Убыточная сделка',
                    'new_capital': self.current_capital,
                    'growth_factor': self.current_capital / self.initial_capital,
                    'total_return_pct': (self.current_capital - self.initial_capital) / self.initial_capital * 100
                }
            
        except Exception as e:
            logger.error(f"Ошибка обработки результата сделки: {e}")
            return {'reinvested': False, 'error': str(e)}
    
    def calculate_profit_taking_levels(self, entry_price: float, signal_direction: str) -> List[float]:
        """Расчет уровней фиксации прибыли с учетом составного роста"""
        try:
            # Базовые уровни из конфигурации
            base_levels = self.config.profit_taking_levels.copy()
            
            # Коэффициент роста для увеличения целей
            growth_factor = self.current_capital / self.initial_capital if self.initial_capital > 0 else 1.0
            growth_multiplier = 1.0 + min(np.log(growth_factor) * 0.1, 0.5)  # Максимум +50%
            
            # Корректируем уровни
            adjusted_levels = [level * growth_multiplier for level in base_levels]
            
            # Рассчитываем цены
            if signal_direction == 'buy':
                profit_prices = [entry_price * (1 + level) for level in adjusted_levels]
            else:  # sell
                profit_prices = [entry_price * (1 - level) for level in adjusted_levels]
            
            logger.debug(f"Уровни фиксации прибыли: {[f'{level:.1%}' for level in adjusted_levels]}")
            
            return profit_prices
            
        except Exception as e:
            logger.error(f"Ошибка расчета уровней фиксации прибыли: {e}")
            return [entry_price * 1.1, entry_price * 1.2, entry_price * 1.3]  # Дефолтные уровни
    
    def get_compound_statistics(self) -> Dict:
        """Получение статистики составного реинвестирования"""
        try:
            if self.initial_capital == 0:
                return {'error': 'Капитал не инициализирован'}
            
            total_return_pct = (self.current_capital - self.initial_capital) / self.initial_capital * 100
            compound_effect = self.reinvested_amount / self.initial_capital * 100
            
            # Анализ роста по периодам
            growth_analysis = self._analyze_growth_periods()
            
            # Прогноз достижения цели
            target_projection = self._project_target_achievement()
            
            return {
                'initial_capital': self.initial_capital,
                'current_capital': self.current_capital,
                'total_profit': self.total_profit,
                'reinvested_amount': self.reinvested_amount,
                'total_return_pct': total_return_pct,
                'compound_effect_pct': compound_effect,
                'growth_factor': self.current_capital / self.initial_capital,
                'compounding_mode': self.mode.value,
                'reinvestment_rate': self.config.reinvestment_percentage,
                'trades_processed': len(self.compound_history),
                'growth_analysis': growth_analysis,
                'target_projection': target_projection,
                'performance_metrics': self._calculate_performance_metrics()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {'error': str(e)}
    
    def _analyze_growth_periods(self) -> Dict:
        """Анализ роста по периодам"""
        try:
            if len(self.compound_history) < 2:
                return {'insufficient_data': True}
            
            # Группируем по дням
            daily_growth = {}
            for record in self.compound_history:
                date = record['timestamp'].date()
                if date not in daily_growth:
                    daily_growth[date] = []
                daily_growth[date].append(record['compound_effect'])
            
            # Рассчитываем статистику
            daily_returns = [sum(effects) for effects in daily_growth.values()]
            
            return {
                'daily_compound_avg': np.mean(daily_returns) if daily_returns else 0,
                'daily_compound_std': np.std(daily_returns) if len(daily_returns) > 1 else 0,
                'best_day': max(daily_returns) if daily_returns else 0,
                'worst_day': min(daily_returns) if daily_returns else 0,
                'positive_days': sum(1 for r in daily_returns if r > 0),
                'total_days': len(daily_returns),
                'consistency_ratio': sum(1 for r in daily_returns if r > 0) / len(daily_returns) if daily_returns else 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа роста: {e}")
            return {'error': str(e)}
    
    def _project_target_achievement(self, target_return: float = 1.0) -> Dict:
        """Прогноз достижения целевой доходности"""
        try:
            current_return = (self.current_capital - self.initial_capital) / self.initial_capital
            
            if current_return >= target_return:
                return {
                    'target_achieved': True,
                    'current_progress': current_return,
                    'target': target_return,
                    'excess_return': current_return - target_return
                }
            
            # Рассчитываем среднюю скорость роста
            if len(self.compound_history) < 2:
                return {'insufficient_data': True}
            
            # Берем последние 10 сделок для расчета тренда
            recent_records = self.compound_history[-10:]
            time_span = (recent_records[-1]['timestamp'] - recent_records[0]['timestamp']).total_seconds() / 86400  # дни
            
            if time_span > 0:
                growth_rate_per_day = (recent_records[-1]['growth_factor'] - recent_records[0]['growth_factor']) / time_span
                
                # Прогноз времени до достижения цели
                remaining_growth = (1 + target_return) - (self.current_capital / self.initial_capital)
                days_to_target = remaining_growth / growth_rate_per_day if growth_rate_per_day > 0 else float('inf')
                
                return {
                    'target_achieved': False,
                    'current_progress': current_return,
                    'target': target_return,
                    'remaining_return': target_return - current_return,
                    'growth_rate_per_day': growth_rate_per_day,
                    'estimated_days_to_target': min(days_to_target, 365),  # Максимум год
                    'probability_assessment': self._assess_achievement_probability(growth_rate_per_day, target_return - current_return)
                }
            
            return {'insufficient_data': True}
            
        except Exception as e:
            logger.error(f"Ошибка прогноза: {e}")
            return {'error': str(e)}
    
    def _assess_achievement_probability(self, growth_rate: float, remaining_return: float) -> str:
        """Оценка вероятности достижения цели"""
        try:
            if growth_rate <= 0:
                return "Очень низкая (отрицательный тренд)"
            
            # Простая эвристика на основе скорости роста
            days_needed = remaining_return / growth_rate
            
            if days_needed <= 7:
                return "Очень высокая (менее недели)"
            elif days_needed <= 30:
                return "Высокая (менее месяца)"
            elif days_needed <= 90:
                return "Средняя (2-3 месяца)"
            elif days_needed <= 180:
                return "Низкая (4-6 месяцев)"
            else:
                return "Очень низкая (более 6 месяцев)"
                
        except Exception as e:
            return f"Ошибка оценки: {str(e)}"
    
    def _calculate_performance_metrics(self) -> Dict:
        """Расчет метрик производительности"""
        try:
            if len(self.compound_history) < 2:
                return {'insufficient_data': True}
            
            # Извлекаем данные для анализа
            returns = [record['compound_effect'] / 100 for record in self.compound_history]  # В долях
            growth_factors = [record['growth_factor'] for record in self.compound_history]
            
            # Основные метрики
            total_return = growth_factors[-1] - 1 if growth_factors else 0
            avg_return = np.mean(returns) if returns else 0
            volatility = np.std(returns) if len(returns) > 1 else 0
            
            # Sharpe Ratio (упрощенный)
            sharpe_ratio = avg_return / volatility if volatility > 0 else 0
            
            # Maximum Drawdown
            peak = growth_factors[0]
            max_drawdown = 0
            for gf in growth_factors:
                if gf > peak:
                    peak = gf
                drawdown = (peak - gf) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            # Win Rate
            positive_returns = sum(1 for r in returns if r > 0)
            win_rate = positive_returns / len(returns) if returns else 0
            
            return {
                'total_return': total_return,
                'average_compound_return': avg_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'total_trades': len(returns),
                'compound_frequency': self.config.compound_frequency
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета метрик: {e}")
            return {'error': str(e)}
    
    def optimize_compounding_strategy(self) -> Dict:
        """Оптимизация стратегии реинвестирования на основе результатов"""
        try:
            stats = self.get_compound_statistics()
            
            if 'error' in stats:
                return stats
            
            current_performance = stats.get('performance_metrics', {})
            
            recommendations = []
            
            # Анализ винрейта
            win_rate = current_performance.get('win_rate', 0)
            if win_rate < 0.4:
                recommendations.append("Снизить процент реинвестирования до повышения винрейта")
            elif win_rate > 0.7:
                recommendations.append("Можно увеличить агрессивность реинвестирования")
            
            # Анализ волатильности
            volatility = current_performance.get('volatility', 0)
            if volatility > 0.1:  # 10%
                recommendations.append("Высокая волатильность - рассмотреть более консервативный режим")
            
            # Анализ просадки
            max_drawdown = current_performance.get('max_drawdown', 0)
            if max_drawdown > 0.3:  # 30%
                recommendations.append("Большая просадка - усилить риск-менеджмент")
            
            # Анализ роста
            growth_factor = stats.get('growth_factor', 1)
            if growth_factor > 1.5:  # 50% рост
                recommendations.append("Отличный рост - можно увеличить размеры позиций")
            
            return {
                'current_mode': self.mode.value,
                'performance_score': self._calculate_performance_score(current_performance),
                'recommendations': recommendations,
                'suggested_mode': self._suggest_optimal_mode(current_performance),
                'optimization_potential': self._estimate_optimization_potential(stats)
            }
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации: {e}")
            return {'error': str(e)}
    
    def _calculate_performance_score(self, metrics: Dict) -> float:
        """Расчет общего балла производительности"""
        try:
            if not metrics or 'error' in metrics:
                return 0.0
            
            # Веса для разных метрик
            weights = {
                'total_return': 0.3,
                'win_rate': 0.25,
                'sharpe_ratio': 0.2,
                'max_drawdown': -0.25  # Отрицательный вес для просадки
            }
            
            score = 0
            for metric, weight in weights.items():
                value = metrics.get(metric, 0)
                if metric == 'max_drawdown':
                    score += weight * value  # Уже отрицательный вес
                else:
                    score += weight * min(value, 1.0)  # Ограничиваем максимум
            
            return max(0, min(1, score))  # Нормализуем 0-1
            
        except Exception as e:
            logger.error(f"Ошибка расчета балла: {e}")
            return 0.0
    
    def _suggest_optimal_mode(self, metrics: Dict) -> str:
        """Предложение оптимального режима"""
        try:
            win_rate = metrics.get('win_rate', 0)
            volatility = metrics.get('volatility', 0)
            max_drawdown = metrics.get('max_drawdown', 0)
            
            # Логика выбора режима
            if win_rate > 0.7 and volatility < 0.05 and max_drawdown < 0.2:
                return CompoundingMode.EXTREME.value
            elif win_rate > 0.6 and volatility < 0.08 and max_drawdown < 0.3:
                return CompoundingMode.AGGRESSIVE.value
            elif win_rate > 0.5 and volatility < 0.12:
                return CompoundingMode.MODERATE.value
            else:
                return CompoundingMode.CONSERVATIVE.value
                
        except Exception as e:
            logger.error(f"Ошибка предложения режима: {e}")
            return CompoundingMode.CONSERVATIVE.value
    
    def _estimate_optimization_potential(self, stats: Dict) -> Dict:
        """Оценка потенциала оптимизации"""
        try:
            current_return = stats.get('total_return_pct', 0)
            
            # Простая оценка потенциала
            if current_return < 10:
                potential = "Высокий"
                description = "Много возможностей для улучшения"
            elif current_return < 50:
                potential = "Средний"
                description = "Есть возможности для оптимизации"
            elif current_return < 100:
                potential = "Низкий"
                description = "Хорошие результаты, небольшие улучшения возможны"
            else:
                potential = "Минимальный"
                description = "Отличные результаты, цель достигнута"
            
            return {
                'level': potential,
                'description': description,
                'estimated_improvement': max(0, 100 - current_return) * 0.1  # 10% от оставшегося потенциала
            }
            
        except Exception as e:
            logger.error(f"Ошибка оценки потенциала: {e}")
            return {'level': 'Неизвестно', 'description': 'Ошибка анализа'}

# Глобальные экземпляры для разных режимов
conservative_compounder = CompoundReinvestmentEngine(CompoundingMode.CONSERVATIVE)
moderate_compounder = CompoundReinvestmentEngine(CompoundingMode.MODERATE)
aggressive_compounder = CompoundReinvestmentEngine(CompoundingMode.AGGRESSIVE)
extreme_compounder = CompoundReinvestmentEngine(CompoundingMode.EXTREME) 