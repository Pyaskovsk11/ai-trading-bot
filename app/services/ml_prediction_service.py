#!/usr/bin/env python3
"""
ML Prediction Service - Сервис машинного обучения для предсказания цен
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
from enum import Enum

# ML библиотеки
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

logger = logging.getLogger(__name__)

class PredictionModel(Enum):
    """Типы моделей предсказания"""
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    ENSEMBLE = "ensemble"

class PredictionHorizon(Enum):
    """Горизонты предсказания"""
    SHORT_TERM = "5m"    # 5 минут
    MEDIUM_TERM = "1h"   # 1 час
    LONG_TERM = "4h"     # 4 часа

@dataclass
class PredictionResult:
    """Результат предсказания"""
    symbol: str
    current_price: float
    predicted_price: float
    confidence: float
    direction: str  # 'up', 'down', 'sideways'
    change_pct: float
    horizon: str
    timestamp: datetime
    features_used: List[str]

@dataclass
class ModelMetrics:
    """Метрики модели"""
    mse: float
    mae: float
    r2_score: float
    accuracy: float
    precision: float
    recall: float

class MLPredictionService:
    """
    Сервис машинного обучения для предсказания цен
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_columns = []
        self.is_trained = False
        
        if not ML_AVAILABLE:
            logger.warning("ML библиотеки не установлены. Используется упрощенная версия.")
        
        logger.info("MLPredictionService инициализирован")
    
    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Создание признаков для ML модели"""
        features_df = df.copy()
        
        # Технические индикаторы
        # RSI
        delta = features_df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features_df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = features_df['close'].ewm(span=12).mean()
        ema_26 = features_df['close'].ewm(span=26).mean()
        features_df['macd'] = ema_12 - ema_26
        features_df['macd_signal'] = features_df['macd'].ewm(span=9).mean()
        features_df['macd_histogram'] = features_df['macd'] - features_df['macd_signal']
        
        # Bollinger Bands
        bb_period = 20
        bb_middle = features_df['close'].rolling(bb_period).mean()
        bb_std = features_df['close'].rolling(bb_period).std()
        features_df['bb_upper'] = bb_middle + (bb_std * 2)
        features_df['bb_lower'] = bb_middle - (bb_std * 2)
        features_df['bb_width'] = (features_df['bb_upper'] - features_df['bb_lower']) / bb_middle
        features_df['bb_position'] = (features_df['close'] - features_df['bb_lower']) / (features_df['bb_upper'] - features_df['bb_lower'])
        
        # Скользящие средние
        for period in [5, 10, 20, 50]:
            features_df[f'sma_{period}'] = features_df['close'].rolling(period).mean()
            features_df[f'ema_{period}'] = features_df['close'].ewm(span=period).mean()
            features_df[f'price_to_sma_{period}'] = features_df['close'] / features_df[f'sma_{period}']
        
        # Ценовые изменения
        for period in [1, 3, 5, 10]:
            features_df[f'return_{period}'] = features_df['close'].pct_change(period)
            features_df[f'high_low_ratio_{period}'] = (features_df['high'] - features_df['low']) / features_df['close']
        
        # Объемные индикаторы
        features_df['volume_sma'] = features_df['volume'].rolling(20).mean()
        features_df['volume_ratio'] = features_df['volume'] / features_df['volume_sma']
        features_df['price_volume'] = features_df['close'] * features_df['volume']
        
        # Волатильность
        features_df['volatility_5'] = features_df['close'].pct_change().rolling(5).std()
        features_df['volatility_20'] = features_df['close'].pct_change().rolling(20).std()
        
        # Временные признаки
        features_df['hour'] = features_df.index.hour
        features_df['day_of_week'] = features_df.index.dayofweek
        features_df['month'] = features_df.index.month
        
        # Лаговые признаки
        for lag in [1, 2, 3, 5]:
            features_df[f'close_lag_{lag}'] = features_df['close'].shift(lag)
            features_df[f'volume_lag_{lag}'] = features_df['volume'].shift(lag)
        
        return features_df
    
    def _prepare_training_data(self, df: pd.DataFrame, horizon: str = "1h") -> Tuple[np.ndarray, np.ndarray]:
        """Подготовка данных для обучения"""
        # Создаем признаки
        features_df = self._create_features(df)
        
        # Определяем горизонт предсказания
        horizon_map = {"5m": 1, "1h": 12, "4h": 48}  # для 5-минутных данных
        shift_periods = horizon_map.get(horizon, 12)
        
        # Создаем целевую переменную (будущая цена)
        features_df['target'] = features_df['close'].shift(-shift_periods)
        
        # Удаляем строки с NaN
        features_df = features_df.dropna()
        
        # Выбираем признаки для модели
        feature_columns = [col for col in features_df.columns 
                          if col not in ['open', 'high', 'low', 'close', 'volume', 'target', 'timestamp']]
        
        self.feature_columns = feature_columns
        
        X = features_df[feature_columns].values
        y = features_df['target'].values
        
        return X, y
    
    async def train_models(self, historical_data: Dict[str, pd.DataFrame], horizon: str = "1h") -> Dict[str, ModelMetrics]:
        """Обучение ML моделей"""
        if not ML_AVAILABLE:
            logger.warning("ML библиотеки недоступны. Пропускаем обучение.")
            return {}
        
        logger.info(f"🤖 Начинаем обучение ML моделей для горизонта {horizon}")
        
        all_metrics = {}
        
        for symbol, df in historical_data.items():
            if len(df) < 200:  # Недостаточно данных
                logger.warning(f"Недостаточно данных для обучения {symbol}: {len(df)} строк")
                continue
            
            try:
                # Подготавливаем данные
                X, y = self._prepare_training_data(df, horizon)
                
                if len(X) < 100:
                    logger.warning(f"Недостаточно обработанных данных для {symbol}: {len(X)} строк")
                    continue
                
                # Разделяем на обучающую и тестовую выборки
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42, shuffle=False
                )
                
                # Масштабируем данные
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                # Создаем и обучаем модели
                models = {
                    'linear_regression': LinearRegression(),
                    'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                    'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
                }
                
                symbol_models = {}
                symbol_metrics = {}
                
                for model_name, model in models.items():
                    # Обучаем модель
                    if model_name == 'linear_regression':
                        model.fit(X_train_scaled, y_train)
                        y_pred = model.predict(X_test_scaled)
                    else:
                        model.fit(X_train, y_train)
                        y_pred = model.predict(X_test)
                    
                    # Рассчитываем метрики
                    mse = mean_squared_error(y_test, y_pred)
                    mae = mean_absolute_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)
                    
                    # Рассчитываем точность направления
                    direction_actual = np.sign(y_test - X_test[:, self.feature_columns.index('close_lag_1')])
                    direction_pred = np.sign(y_pred - X_test[:, self.feature_columns.index('close_lag_1')])
                    accuracy = np.mean(direction_actual == direction_pred)
                    
                    metrics = ModelMetrics(
                        mse=mse, mae=mae, r2_score=r2, 
                        accuracy=accuracy, precision=0.0, recall=0.0
                    )
                    
                    symbol_models[model_name] = model
                    symbol_metrics[model_name] = metrics
                    
                    logger.info(f"   {symbol} {model_name}: R²={r2:.3f}, Accuracy={accuracy:.3f}")
                
                # Сохраняем модели и скейлер
                self.models[symbol] = symbol_models
                self.scalers[symbol] = scaler
                all_metrics[symbol] = symbol_metrics
                
            except Exception as e:
                logger.error(f"Ошибка обучения модели для {symbol}: {e}")
        
        self.is_trained = len(self.models) > 0
        logger.info(f"✅ Обучение завершено. Модели для {len(self.models)} символов")
        
        return all_metrics
    
    async def predict_price(self, symbol: str, current_data: pd.DataFrame, horizon: str = "1h") -> Optional[PredictionResult]:
        """Предсказание цены для символа"""
        if not self.is_trained or symbol not in self.models:
            # Используем простое предсказание на основе трендов
            return self._simple_prediction(symbol, current_data, horizon)
        
        if not ML_AVAILABLE:
            return self._simple_prediction(symbol, current_data, horizon)
        
        try:
            # Создаем признаки
            features_df = self._create_features(current_data)
            
            if len(features_df) == 0:
                return None
            
            # Берем последнюю строку
            latest_features = features_df[self.feature_columns].iloc[-1:].values
            
            # Масштабируем данные
            scaler = self.scalers[symbol]
            latest_features_scaled = scaler.transform(latest_features)
            
            # Получаем предсказания от всех моделей
            models = self.models[symbol]
            predictions = []
            
            for model_name, model in models.items():
                if model_name == 'linear_regression':
                    pred = model.predict(latest_features_scaled)[0]
                else:
                    pred = model.predict(latest_features)[0]
                predictions.append(pred)
            
            # Ансамблевое предсказание (среднее)
            predicted_price = np.mean(predictions)
            current_price = current_data['close'].iloc[-1]
            
            # Рассчитываем уверенность на основе согласованности моделей
            prediction_std = np.std(predictions)
            confidence = max(0.1, 1.0 - (prediction_std / current_price))
            
            # Определяем направление
            change_pct = (predicted_price - current_price) / current_price * 100
            
            if abs(change_pct) < 0.1:
                direction = 'sideways'
            elif change_pct > 0:
                direction = 'up'
            else:
                direction = 'down'
            
            return PredictionResult(
                symbol=symbol,
                current_price=current_price,
                predicted_price=predicted_price,
                confidence=confidence,
                direction=direction,
                change_pct=change_pct,
                horizon=horizon,
                timestamp=datetime.now(),
                features_used=self.feature_columns
            )
            
        except Exception as e:
            logger.error(f"Ошибка предсказания для {symbol}: {e}")
            return self._simple_prediction(symbol, current_data, horizon)
    
    def _simple_prediction(self, symbol: str, current_data: pd.DataFrame, horizon: str) -> PredictionResult:
        """Простое предсказание на основе трендов"""
        if len(current_data) < 20:
            return None
        
        current_price = current_data['close'].iloc[-1]
        
        # Простой анализ тренда
        short_ma = current_data['close'].rolling(5).mean().iloc[-1]
        long_ma = current_data['close'].rolling(20).mean().iloc[-1]
        
        # Волатильность
        volatility = current_data['close'].pct_change().rolling(10).std().iloc[-1]
        
        # Простое предсказание на основе тренда
        if short_ma > long_ma:
            # Восходящий тренд
            predicted_change = volatility * 0.5  # 50% от волатильности
            direction = 'up'
        elif short_ma < long_ma:
            # Нисходящий тренд
            predicted_change = -volatility * 0.5
            direction = 'down'
        else:
            # Боковой тренд
            predicted_change = 0
            direction = 'sideways'
        
        predicted_price = current_price * (1 + predicted_change)
        change_pct = predicted_change * 100
        confidence = 0.3  # Низкая уверенность для простого предсказания
        
        return PredictionResult(
            symbol=symbol,
            current_price=current_price,
            predicted_price=predicted_price,
            confidence=confidence,
            direction=direction,
            change_pct=change_pct,
            horizon=horizon,
            timestamp=datetime.now(),
            features_used=['simple_trend_analysis']
        )
    
    async def get_trading_signals(self, predictions: List[PredictionResult], min_confidence: float = 0.6) -> List[Dict]:
        """Генерация торговых сигналов на основе предсказаний"""
        signals = []
        
        for pred in predictions:
            if pred.confidence < min_confidence:
                continue
            
            # Определяем силу сигнала
            signal_strength = abs(pred.change_pct) * pred.confidence
            
            if signal_strength < 0.5:  # Слабый сигнал
                continue
            
            signal = {
                'symbol': pred.symbol,
                'signal': 'buy' if pred.direction == 'up' else 'sell' if pred.direction == 'down' else 'hold',
                'confidence': pred.confidence,
                'predicted_change': pred.change_pct,
                'horizon': pred.horizon,
                'strategy_type': 'ml_prediction',
                'reason': f"ML предсказание: {pred.direction} на {pred.change_pct:.2f}% (уверенность: {pred.confidence:.2f})",
                'should_execute': signal_strength > 1.0  # Выполняем только сильные сигналы
            }
            
            signals.append(signal)
        
        return signals
    
    def save_models(self, filepath: str):
        """Сохранение обученных моделей"""
        if not ML_AVAILABLE or not self.is_trained:
            logger.warning("Нет моделей для сохранения")
            return
        
        try:
            model_data = {
                'models': self.models,
                'scalers': self.scalers,
                'feature_columns': self.feature_columns,
                'is_trained': self.is_trained
            }
            
            joblib.dump(model_data, filepath)
            logger.info(f"Модели сохранены в {filepath}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения моделей: {e}")
    
    def load_models(self, filepath: str):
        """Загрузка обученных моделей"""
        if not ML_AVAILABLE:
            logger.warning("ML библиотеки недоступны")
            return
        
        try:
            model_data = joblib.load(filepath)
            
            self.models = model_data['models']
            self.scalers = model_data['scalers']
            self.feature_columns = model_data['feature_columns']
            self.is_trained = model_data['is_trained']
            
            logger.info(f"Модели загружены из {filepath}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки моделей: {e}")

# Глобальный экземпляр
ml_prediction_service = MLPredictionService() 