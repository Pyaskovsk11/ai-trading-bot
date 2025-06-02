import numpy as np
import pandas as pd
import tensorflow as tf

# Включаем eager execution для исправления ошибки numpy()
tf.config.run_functions_eagerly(True)

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import accuracy_score, classification_report
import joblib
import logging
from typing import Tuple, List, Optional
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class LSTMTradingModel:
    """
    LSTM модель для предсказания направления движения цены криптовалют
    """
    
    def __init__(self, sequence_length: int = 60, features: int = 6, model_path: str = "models/lstm"):
        self.sequence_length = sequence_length
        self.features = features
        self.model_path = model_path
        self.model = None
        self.scaler = MinMaxScaler()
        self.is_trained = False
        
        # Создаем директорию для моделей
        os.makedirs(model_path, exist_ok=True)
        
        logger.info(f"Инициализирована LSTM модель: sequence_length={sequence_length}, features={features}")
    
    def _build_lstm_model(self) -> Sequential:
        """Создание архитектуры LSTM модели"""
        # Очищаем сессию TensorFlow для избежания конфликтов с оптимизатором
        tf.keras.backend.clear_session()
        
        model = Sequential([
            # Первый LSTM слой с возвратом последовательностей
            LSTM(50, return_sequences=True, input_shape=(self.sequence_length, self.features)),
            Dropout(0.2),
            
            # Второй LSTM слой
            LSTM(50, return_sequences=True),
            Dropout(0.2),
            
            # Третий LSTM слой
            LSTM(50),
            Dropout(0.2),
            
            # Полносвязные слои
            Dense(25, activation='relu'),
            Dense(1, activation='sigmoid')  # Вероятность роста цены (0-1)
        ])
        
        # Компиляция модели с новым оптимизатором
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info("LSTM модель создана и скомпилирована")
        return model
    
    def prepare_sequences(self, data: pd.DataFrame, target_column: str = 'close') -> Tuple[np.ndarray, np.ndarray]:
        """
        Подготовка последовательностей для обучения LSTM
        
        Args:
            data: DataFrame с историческими данными
            target_column: Колонка для предсказания
            
        Returns:
            X: Последовательности признаков
            y: Целевые значения (1 - рост, 0 - падение)
        """
        # Создаем целевую переменную (1 если цена выросла, 0 если упала)
        data = data.copy()
        data['target'] = (data[target_column].shift(-1) > data[target_column]).astype(int)
        
        # Удаляем последнюю строку (нет целевого значения)
        data = data[:-1]
        
        # Выбираем признаки для модели
        feature_columns = [col for col in data.columns if col not in ['target', 'timestamp']]
        features_data = data[feature_columns].values
        targets = data['target'].values
        
        # Нормализация данных
        features_scaled = self.scaler.fit_transform(features_data)
        
        # Создание последовательностей
        X, y = [], []
        for i in range(self.sequence_length, len(features_scaled)):
            X.append(features_scaled[i-self.sequence_length:i])
            y.append(targets[i])
        
        X = np.array(X)
        y = np.array(y)
        
        logger.info(f"Подготовлено {len(X)} последовательностей для обучения")
        return X, y
    
    def train(self, X: np.ndarray, y: np.ndarray, validation_split: float = 0.2, 
              epochs: int = 50, batch_size: int = 32) -> dict:
        """
        Обучение LSTM модели
        
        Args:
            X: Последовательности признаков
            y: Целевые значения
            validation_split: Доля данных для валидации
            epochs: Количество эпох обучения
            batch_size: Размер батча
            
        Returns:
            История обучения
        """
        try:
            # Принудительно пересоздаем модель для избежания проблем с оптимизатором
            logger.info("Создание новой LSTM модели для обучения...")
            self.model = self._build_lstm_model()
            
            logger.info(f"Начинаем обучение LSTM модели на {len(X)} примерах")
            
            # Обучение модели
            history = self.model.fit(
                X, y,
                validation_split=validation_split,
                epochs=epochs,
                batch_size=batch_size,
                verbose=1,
                shuffle=True
            )
            
            self.is_trained = True
            
            # Сохранение модели
            self.save_model()
            
            # Оценка качества на валидационных данных
            val_predictions = self.model.predict(X[-int(len(X) * validation_split):])
            val_predictions_binary = (val_predictions > 0.5).astype(int)
            val_true = y[-int(len(y) * validation_split):]
            
            accuracy = accuracy_score(val_true, val_predictions_binary)
            logger.info(f"Точность модели на валидации: {accuracy:.4f}")
            
            return {
                'history': history.history,
                'validation_accuracy': accuracy,
                'training_samples': len(X)
            }
            
        except Exception as e:
            logger.error(f"Ошибка обучения LSTM модели: {e}")
            # Очищаем состояние при ошибке
            tf.keras.backend.clear_session()
            self.model = None
            self.is_trained = False
            raise e
    
    def predict(self, sequence: np.ndarray) -> Tuple[float, float]:
        """
        Предсказание направления цены для одной последовательности
        
        Args:
            sequence: Последовательность признаков (sequence_length, features)
            
        Returns:
            probability: Вероятность роста цены (0-1)
            confidence: Уверенность в предсказании
        """
        if not self.is_trained or self.model is None:
            logger.warning("Модель не обучена")
            return 0.5, 0.0
        
        # Нормализация входной последовательности
        sequence_scaled = self.scaler.transform(sequence)
        sequence_scaled = sequence_scaled.reshape(1, self.sequence_length, self.features)
        
        # Предсказание
        probability = float(self.model.predict(sequence_scaled, verbose=0)[0][0])
        
        # Расчет уверенности (расстояние от 0.5)
        confidence = abs(probability - 0.5) * 2
        
        return probability, confidence
    
    def predict_batch(self, sequences: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Предсказание для батча последовательностей
        
        Args:
            sequences: Батч последовательностей (batch_size, sequence_length, features)
            
        Returns:
            probabilities: Вероятности роста цены
            confidences: Уверенности в предсказаниях
        """
        if not self.is_trained or self.model is None:
            logger.warning("Модель не обучена")
            return np.array([0.5] * len(sequences)), np.array([0.0] * len(sequences))
        
        # Нормализация
        sequences_scaled = np.array([self.scaler.transform(seq) for seq in sequences])
        
        # Предсказания
        probabilities = self.model.predict(sequences_scaled, verbose=0).flatten()
        
        # Уверенности
        confidences = np.abs(probabilities - 0.5) * 2
        
        return probabilities, confidences
    
    def save_model(self):
        """Сохранение модели и скейлера"""
        if self.model is not None:
            model_file = os.path.join(self.model_path, "lstm_model.h5")
            scaler_file = os.path.join(self.model_path, "scaler.pkl")
            
            self.model.save(model_file)
            joblib.dump(self.scaler, scaler_file)
            
            # Сохраняем метаданные
            metadata = {
                'sequence_length': self.sequence_length,
                'features': self.features,
                'is_trained': self.is_trained,
                'saved_at': datetime.now().isoformat()
            }
            metadata_file = os.path.join(self.model_path, "metadata.pkl")
            joblib.dump(metadata, metadata_file)
            
            logger.info(f"Модель сохранена в {self.model_path}")
    
    def load_model(self) -> bool:
        """
        Загрузка сохраненной модели
        
        Returns:
            True если модель успешно загружена
        """
        try:
            from tensorflow.keras.models import load_model
            
            model_file = os.path.join(self.model_path, "lstm_model.h5")
            scaler_file = os.path.join(self.model_path, "scaler.pkl")
            metadata_file = os.path.join(self.model_path, "metadata.pkl")
            
            if all(os.path.exists(f) for f in [model_file, scaler_file, metadata_file]):
                self.model = load_model(model_file)
                self.scaler = joblib.load(scaler_file)
                metadata = joblib.load(metadata_file)
                
                self.sequence_length = metadata['sequence_length']
                self.features = metadata['features']
                self.is_trained = metadata['is_trained']
                
                logger.info(f"Модель загружена из {self.model_path}")
                return True
            else:
                logger.warning("Файлы модели не найдены")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            return False
    
    def get_model_info(self) -> dict:
        """Получение информации о модели"""
        return {
            'sequence_length': self.sequence_length,
            'features': self.features,
            'is_trained': self.is_trained,
            'model_path': self.model_path,
            'model_exists': self.model is not None
        }
    
    def evaluate_model(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """
        Оценка качества модели на тестовых данных
        
        Args:
            X_test: Тестовые последовательности
            y_test: Тестовые целевые значения
            
        Returns:
            Метрики качества модели
        """
        if not self.is_trained or self.model is None:
            return {'error': 'Модель не обучена'}
        
        # Предсказания
        predictions = self.model.predict(X_test, verbose=0)
        predictions_binary = (predictions > 0.5).astype(int).flatten()
        
        # Метрики
        accuracy = accuracy_score(y_test, predictions_binary)
        
        # Дополнительные метрики
        from sklearn.metrics import precision_score, recall_score, f1_score
        
        precision = precision_score(y_test, predictions_binary, zero_division=0)
        recall = recall_score(y_test, predictions_binary, zero_division=0)
        f1 = f1_score(y_test, predictions_binary, zero_division=0)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'test_samples': len(X_test)
        } 