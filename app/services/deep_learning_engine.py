import numpy as np
import pandas as pd
import logging
from typing import Dict, Tuple, Optional, List
from datetime import datetime, timedelta
import asyncio
import joblib
import os

from .lstm_model import LSTMTradingModel
from .cnn_patterns import CandlestickCNN

logger = logging.getLogger(__name__)

class DeepLearningEngine:
    """
    Базовый движок для Deep Learning моделей в торговой системе
    Объединяет LSTM и CNN модели для комплексного анализа
    """
    
    def __init__(self, models_path: str = "models"):
        self.models_path = models_path
        self.lstm_model = LSTMTradingModel(model_path=f"{models_path}/lstm")
        self.cnn_model = CandlestickCNN(model_path=f"{models_path}/cnn")
        
        # Веса для комбинирования сигналов
        self.model_weights = {
            'lstm': 0.6,  # LSTM получает больший вес для временных рядов
            'cnn': 0.4    # CNN для паттернов свечей
        }
        
        # Кэш для предсказаний
        self.prediction_cache = {}
        self.cache_ttl = 300  # 5 минут
        
        # Создаем директории
        os.makedirs(models_path, exist_ok=True)
        
        logger.info("Инициализирован Deep Learning Engine")
    
    async def initialize_models(self) -> Dict[str, bool]:
        """
        Инициализация и загрузка моделей
        
        Returns:
            Статус загрузки каждой модели
        """
        results = {}
        
        try:
            # Попытка загрузить LSTM модель
            lstm_loaded = self.lstm_model.load_model()
            results['lstm'] = lstm_loaded
            
            if not lstm_loaded:
                logger.info("LSTM модель не найдена, будет создана при первом обучении")
            
            # Попытка загрузить CNN модель
            cnn_loaded = self.cnn_model.load_model()
            results['cnn'] = cnn_loaded
            
            if not cnn_loaded:
                logger.info("CNN модель не найдена, будет создана при первом обучении")
            
            logger.info(f"Статус загрузки моделей: {results}")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации моделей: {e}")
            results = {'lstm': False, 'cnn': False, 'error': str(e)}
        
        return results
    
    def prepare_features_for_lstm(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Подготовка признаков для LSTM модели
        
        Args:
            data: Исходные OHLCV данные
            
        Returns:
            DataFrame с признаками для LSTM
        """
        df = data.copy()
        
        # Технические индикаторы
        # Скользящие средние
        df['sma_5'] = df['close'].rolling(5).mean()
        df['sma_10'] = df['close'].rolling(10).mean()
        df['sma_20'] = df['close'].rolling(20).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Объем
        df['volume_sma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Ценовые изменения
        df['price_change'] = df['close'].pct_change()
        df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        df['open_close_ratio'] = (df['close'] - df['open']) / df['open']
        
        # Волатильность
        df['volatility'] = df['price_change'].rolling(20).std()
        
        # Удаляем NaN значения
        df = df.dropna()
        
        # ИСПРАВЛЕНИЕ: Используем только 6 основных признаков для совместимости с существующей моделью
        # Это исправляет ошибку "X has 20 features, but MinMaxScaler is expecting 6 features"
        feature_columns = [
            'close',      # Цена закрытия
            'volume',     # Объем
            'rsi',        # RSI индикатор
            'macd',       # MACD
            'bb_position', # Позиция в Bollinger Bands
            'volatility'  # Волатильность
        ]
        
        # Проверяем наличие всех колонок
        available_columns = [col for col in feature_columns if col in df.columns]
        
        # Убеждаемся, что у нас ровно 6 признаков для совместимости
        if len(available_columns) != 6:
            logger.warning(f"Ожидалось 6 признаков, получено {len(available_columns)}")
            # Дополняем недостающие признаки как нули
            for i, col in enumerate(feature_columns):
                if col not in df.columns:
                    df[col] = 0.0
                    logger.warning(f"Добавлен признак {col} как 0.0")
            available_columns = feature_columns
        
        logger.info(f"Подготовлено {len(available_columns)} признаков для LSTM: {available_columns}")
        return df[available_columns]
    
    async def train_models(self, data: pd.DataFrame, epochs: int = 50) -> Dict[str, Dict]:
        """
        Обучение всех моделей
        
        Args:
            data: Исходные OHLCV данные
            epochs: Количество эпох обучения
            
        Returns:
            Результаты обучения каждой модели
        """
        results = {}
        
        try:
            # Подготовка данных для LSTM
            logger.info("Подготовка данных для обучения LSTM...")
            lstm_features = self.prepare_features_for_lstm(data)
            
            if len(lstm_features) < 100:
                raise ValueError("Недостаточно данных для обучения (минимум 100 записей)")
            
            # Обучение LSTM
            logger.info("Обучение LSTM модели...")
            X_lstm, y_lstm = self.lstm_model.prepare_sequences(lstm_features)
            lstm_result = self.lstm_model.train(X_lstm, y_lstm, epochs=epochs)
            results['lstm'] = lstm_result
            
            # Подготовка данных для CNN
            logger.info("Подготовка данных для обучения CNN...")
            ohlcv_data = data[['open', 'high', 'low', 'close', 'volume']].copy()
            
            # Обучение CNN
            logger.info("Обучение CNN модели...")
            X_cnn, y_cnn = self.cnn_model.prepare_candlestick_images(ohlcv_data)
            cnn_result = self.cnn_model.train(X_cnn, y_cnn, epochs=epochs)
            results['cnn'] = cnn_result
            
            logger.info("Обучение всех моделей завершено успешно")
            
        except Exception as e:
            logger.error(f"Ошибка обучения моделей: {e}")
            results['error'] = str(e)
        
        return results
    
    async def get_prediction(self, data: pd.DataFrame, symbol: str = "BTC/USDT") -> Dict:
        """
        Получение комбинированного предсказания от всех моделей
        
        Args:
            data: Последние данные для анализа
            symbol: Торговая пара
            
        Returns:
            Комбинированное предсказание
        """
        cache_key = f"{symbol}_{len(data)}"
        current_time = datetime.now()
        
        # Проверяем кэш
        if cache_key in self.prediction_cache:
            cached_data = self.prediction_cache[cache_key]
            if (current_time - cached_data['timestamp']).seconds < self.cache_ttl:
                return cached_data['prediction']
        
        try:
            prediction_result = {
                'symbol': symbol,
                'timestamp': current_time.isoformat(),
                'models': {},
                'combined': {}
            }
            
            # LSTM предсказание
            if self.lstm_model.is_trained:
                lstm_features = self.prepare_features_for_lstm(data)
                
                if len(lstm_features) >= self.lstm_model.sequence_length:
                    # Берем последнюю последовательность
                    last_sequence = lstm_features.tail(self.lstm_model.sequence_length).values
                    lstm_prob, lstm_conf = self.lstm_model.predict(last_sequence)
                    
                    prediction_result['models']['lstm'] = {
                        'probability': float(lstm_prob),
                        'confidence': float(lstm_conf),
                        'signal': 'buy' if lstm_prob > 0.6 else 'sell' if lstm_prob < 0.4 else 'hold'
                    }
                else:
                    prediction_result['models']['lstm'] = {
                        'error': 'Недостаточно данных для LSTM предсказания'
                    }
            else:
                prediction_result['models']['lstm'] = {
                    'error': 'LSTM модель не обучена'
                }
            
            # CNN предсказание
            if self.cnn_model.is_trained:
                ohlcv_data = data[['open', 'high', 'low', 'close', 'volume']].copy()
                
                if len(ohlcv_data) >= 20:
                    cnn_analysis = self.cnn_model.analyze_ohlcv_patterns(ohlcv_data)
                    
                    prediction_result['models']['cnn'] = {
                        'pattern': cnn_analysis.get('pattern', 'neutral'),
                        'confidence': float(cnn_analysis.get('confidence', 0.0)),
                        'last_candle_type': cnn_analysis.get('last_candle_type', 'neutral'),
                        'trend_strength': float(cnn_analysis.get('trend_strength', 0.0))
                    }
                else:
                    prediction_result['models']['cnn'] = {
                        'error': 'Недостаточно данных для CNN анализа'
                    }
            else:
                prediction_result['models']['cnn'] = {
                    'error': 'CNN модель не обучена'
                }
            
            # Комбинированное предсказание
            combined_signal, combined_confidence = self._combine_predictions(prediction_result['models'])
            
            prediction_result['combined'] = {
                'signal': combined_signal,
                'confidence': combined_confidence,
                'recommendation': self._get_recommendation(combined_signal, combined_confidence)
            }
            
            # Сохраняем в кэш
            self.prediction_cache[cache_key] = {
                'prediction': prediction_result,
                'timestamp': current_time
            }
            
            return prediction_result
            
        except Exception as e:
            logger.error(f"Ошибка получения предсказания: {e}")
            return {
                'error': str(e),
                'timestamp': current_time.isoformat()
            }
    
    def _combine_predictions(self, models_predictions: Dict) -> Tuple[str, float]:
        """
        Комбинирование предсказаний от разных моделей
        
        Args:
            models_predictions: Предсказания от моделей
            
        Returns:
            Комбинированный сигнал и уверенность
        """
        signals = []
        confidences = []
        weights = []
        
        # LSTM сигнал
        if 'lstm' in models_predictions and 'probability' in models_predictions['lstm']:
            lstm_data = models_predictions['lstm']
            lstm_prob = lstm_data['probability']
            lstm_conf = lstm_data['confidence']
            
            # Конвертируем вероятность в сигнал
            if lstm_prob > 0.6:
                signals.append(1)  # buy
            elif lstm_prob < 0.4:
                signals.append(-1)  # sell
            else:
                signals.append(0)  # hold
            
            confidences.append(lstm_conf)
            weights.append(self.model_weights['lstm'])
        
        # CNN сигнал
        if 'cnn' in models_predictions and 'pattern' in models_predictions['cnn']:
            cnn_data = models_predictions['cnn']
            pattern = cnn_data['pattern']
            cnn_conf = cnn_data['confidence']
            
            # Конвертируем паттерн в сигнал
            if pattern == 'bullish':
                signals.append(1)  # buy
            elif pattern == 'bearish':
                signals.append(-1)  # sell
            else:
                signals.append(0)  # hold
            
            confidences.append(cnn_conf)
            weights.append(self.model_weights['cnn'])
        
        if not signals:
            return 'hold', 0.0
        
        # Взвешенное комбинирование
        weighted_signal = sum(s * w for s, w in zip(signals, weights)) / sum(weights)
        combined_confidence = sum(c * w for c, w in zip(confidences, weights)) / sum(weights)
        
        # Определяем итоговый сигнал
        if weighted_signal > 0.3:
            final_signal = 'buy'
        elif weighted_signal < -0.3:
            final_signal = 'sell'
        else:
            final_signal = 'hold'
        
        return final_signal, combined_confidence
    
    def _get_recommendation(self, signal: str, confidence: float) -> str:
        """
        Получение рекомендации на основе сигнала и уверенности
        
        Args:
            signal: Торговый сигнал
            confidence: Уверенность в сигнале
            
        Returns:
            Текстовая рекомендация
        """
        if confidence < 0.3:
            return "Низкая уверенность - рекомендуется дождаться более четкого сигнала"
        elif confidence < 0.6:
            return f"Умеренная уверенность - осторожный {signal}"
        else:
            return f"Высокая уверенность - сильный сигнал {signal}"
    
    def get_models_status(self) -> Dict:
        """Получение статуса всех моделей"""
        return {
            'lstm': self.lstm_model.get_model_info(),
            'cnn': self.cnn_model.get_model_info(),
            'weights': self.model_weights,
            'cache_size': len(self.prediction_cache)
        }
    
    def clear_cache(self):
        """Очистка кэша предсказаний"""
        self.prediction_cache.clear()
        logger.info("Кэш предсказаний очищен")
    
    def update_model_weights(self, new_weights: Dict[str, float]):
        """
        Обновление весов моделей
        
        Args:
            new_weights: Новые веса для моделей
        """
        if 'lstm' in new_weights and 'cnn' in new_weights:
            # Нормализуем веса
            total_weight = new_weights['lstm'] + new_weights['cnn']
            self.model_weights['lstm'] = new_weights['lstm'] / total_weight
            self.model_weights['cnn'] = new_weights['cnn'] / total_weight
            
            logger.info(f"Веса моделей обновлены: {self.model_weights}")
            
            # Очищаем кэш после изменения весов
            self.clear_cache()
    
    async def evaluate_models(self, test_data: pd.DataFrame) -> Dict:
        """
        Оценка качества всех моделей на тестовых данных
        
        Args:
            test_data: Тестовые данные
            
        Returns:
            Метрики качества моделей
        """
        results = {}
        
        try:
            # Оценка LSTM
            if self.lstm_model.is_trained:
                lstm_features = self.prepare_features_for_lstm(test_data)
                X_test, y_test = self.lstm_model.prepare_sequences(lstm_features)
                
                if len(X_test) > 0:
                    lstm_metrics = self.lstm_model.evaluate_model(X_test, y_test)
                    results['lstm'] = lstm_metrics
            
            # Оценка CNN
            if self.cnn_model.is_trained:
                ohlcv_data = test_data[['open', 'high', 'low', 'close', 'volume']].copy()
                X_test_cnn, y_test_cnn = self.cnn_model.prepare_candlestick_images(ohlcv_data)
                
                if len(X_test_cnn) > 0:
                    cnn_metrics = self.cnn_model.evaluate_model(X_test_cnn, y_test_cnn)
                    results['cnn'] = cnn_metrics
            
        except Exception as e:
            logger.error(f"Ошибка оценки моделей: {e}")
            results['error'] = str(e)
        
        return results 