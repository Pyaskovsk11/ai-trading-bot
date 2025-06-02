import numpy as np
import pandas as pd
import tensorflow as tf

# Включаем eager execution для исправления ошибки numpy()
tf.config.run_functions_eagerly(True)

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib
import logging
from typing import Tuple, List, Optional, Dict
import os
from datetime import datetime
import matplotlib.pyplot as plt
from PIL import Image
import cv2

logger = logging.getLogger(__name__)

class CandlestickCNN:
    """
    CNN модель для распознавания паттернов японских свечей
    """
    
    def __init__(self, image_size: int = 64, model_path: str = "models/cnn"):
        self.image_size = image_size
        self.model_path = model_path
        self.model = None
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.pattern_classes = ['bullish', 'bearish', 'neutral']
        
        # Создаем директорию для моделей
        os.makedirs(model_path, exist_ok=True)
        
        logger.info(f"Инициализирована CNN модель: image_size={image_size}")
    
    def _build_cnn_model(self, num_classes: int = 3) -> Sequential:
        """Создание архитектуры CNN модели"""
        # Очищаем сессию TensorFlow для избежания конфликтов с оптимизатором
        tf.keras.backend.clear_session()
        
        model = Sequential([
            # Первый блок свертки
            Conv2D(32, (3, 3), activation='relu', input_shape=(self.image_size, self.image_size, 1)),
            BatchNormalization(),
            MaxPooling2D(2, 2),
            Dropout(0.25),
            
            # Второй блок свертки
            Conv2D(64, (3, 3), activation='relu'),
            BatchNormalization(),
            MaxPooling2D(2, 2),
            Dropout(0.25),
            
            # Третий блок свертки
            Conv2D(128, (3, 3), activation='relu'),
            BatchNormalization(),
            MaxPooling2D(2, 2),
            Dropout(0.25),
            
            # Полносвязные слои
            Flatten(),
            Dense(512, activation='relu'),
            Dropout(0.5),
            Dense(256, activation='relu'),
            Dropout(0.5),
            Dense(num_classes, activation='softmax')  # Buy/Hold/Sell
        ])
        
        # Компиляция модели с новым оптимизатором
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info("CNN модель создана и скомпилирована")
        return model
    
    def prepare_candlestick_images(self, ohlcv_data: pd.DataFrame, window_size: int = 20) -> Tuple[np.ndarray, np.ndarray]:
        """
        Конвертация OHLCV данных в изображения свечей
        
        Args:
            ohlcv_data: DataFrame с OHLCV данными
            window_size: Размер окна для создания изображения
            
        Returns:
            images: Массив изображений
            labels: Метки классов
        """
        images = []
        labels = []
        
        for i in range(window_size, len(ohlcv_data)):
            # Берем окно данных
            window_data = ohlcv_data.iloc[i-window_size:i].copy()
            
            # Создаем изображение свечей
            image = self._create_candlestick_image(window_data)
            
            # Определяем класс на основе следующей свечи
            current_close = ohlcv_data.iloc[i-1]['close']
            next_close = ohlcv_data.iloc[i]['close'] if i < len(ohlcv_data) else current_close
            
            # Классификация: 0 - bearish, 1 - neutral, 2 - bullish
            price_change = (next_close - current_close) / current_close
            if price_change > 0.01:  # Рост больше 1%
                label = 2  # bullish
            elif price_change < -0.01:  # Падение больше 1%
                label = 0  # bearish
            else:
                label = 1  # neutral
            
            images.append(image)
            labels.append(label)
        
        images = np.array(images)
        labels = np.array(labels)
        
        logger.info(f"Создано {len(images)} изображений свечей")
        return images, labels
    
    def _create_candlestick_image(self, data: pd.DataFrame) -> np.ndarray:
        """
        Создание изображения японских свечей из OHLCV данных
        
        Args:
            data: DataFrame с OHLCV данными
            
        Returns:
            Изображение в виде numpy массива
        """
        # Создаем фигуру matplotlib
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_facecolor('black')
        
        # Нормализуем цены
        min_price = data[['open', 'high', 'low', 'close']].min().min()
        max_price = data[['open', 'high', 'low', 'close']].max().max()
        price_range = max_price - min_price
        
        if price_range == 0:
            price_range = 1
        
        # Рисуем свечи
        for i, (idx, row) in enumerate(data.iterrows()):
            open_price = (row['open'] - min_price) / price_range
            high_price = (row['high'] - min_price) / price_range
            low_price = (row['low'] - min_price) / price_range
            close_price = (row['close'] - min_price) / price_range
            
            # Цвет свечи
            color = 'green' if close_price >= open_price else 'red'
            
            # Тело свечи
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            
            # Рисуем тело свечи
            ax.add_patch(plt.Rectangle((i, body_bottom), 0.8, body_height, 
                                     facecolor=color, edgecolor=color))
            
            # Рисуем тени
            ax.plot([i + 0.4, i + 0.4], [low_price, high_price], color=color, linewidth=1)
        
        # Настройки осей
        ax.set_xlim(-0.5, len(data) - 0.5)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.axis('off')
        
        # Конвертируем в изображение
        fig.canvas.draw()
        # Исправляем проблему с matplotlib backend
        try:
            image = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        except AttributeError:
            # Альтернативный метод для некоторых backend'ов
            image = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
            image = image.reshape(fig.canvas.get_width_height()[::-1] + (4,))
            image = image[:, :, :3]  # Убираем alpha канал
        else:
            image = image.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        
        plt.close(fig)
        
        # Конвертируем в градации серого и изменяем размер
        image_gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        image_resized = cv2.resize(image_gray, (self.image_size, self.image_size))
        
        # Нормализация
        image_normalized = image_resized.astype(np.float32) / 255.0
        
        return image_normalized
    
    def train(self, images: np.ndarray, labels: np.ndarray, validation_split: float = 0.2,
              epochs: int = 50, batch_size: int = 32) -> dict:
        """
        Обучение CNN модели
        
        Args:
            images: Массив изображений
            labels: Метки классов
            validation_split: Доля данных для валидации
            epochs: Количество эпох обучения
            batch_size: Размер батча
            
        Returns:
            История обучения
        """
        try:
            # Подготовка данных
            images = images.reshape(-1, self.image_size, self.image_size, 1)
            
            # Принудительно пересоздаем модель для избежания проблем с оптимизатором
            num_classes = len(np.unique(labels))
            logger.info("Создание новой CNN модели для обучения...")
            self.model = self._build_cnn_model(num_classes)
            
            logger.info(f"Начинаем обучение CNN модели на {len(images)} изображениях")
            
            # Обучение модели
            history = self.model.fit(
                images, labels,
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
            val_images = images[-int(len(images) * validation_split):]
            val_labels = labels[-int(len(labels) * validation_split):]
            
            val_predictions = self.model.predict(val_images, verbose=0)
            val_predictions_classes = np.argmax(val_predictions, axis=1)
            
            accuracy = accuracy_score(val_labels, val_predictions_classes)
            logger.info(f"Точность модели на валидации: {accuracy:.4f}")
            
            return {
                'history': history.history,
                'validation_accuracy': accuracy,
                'training_samples': len(images),
                'num_classes': num_classes
            }
            
        except Exception as e:
            logger.error(f"Ошибка обучения CNN модели: {e}")
            # Очищаем состояние при ошибке
            tf.keras.backend.clear_session()
            self.model = None
            self.is_trained = False
            raise e
    
    def detect_patterns(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Детекция паттернов свечей на изображении
        
        Args:
            image: Изображение свечей
            
        Returns:
            pattern: Название паттерна
            confidence: Уверенность в предсказании
        """
        if not self.is_trained or self.model is None:
            logger.warning("Модель не обучена")
            return "neutral", 0.0
        
        # Подготовка изображения
        if len(image.shape) == 2:
            image = image.reshape(1, self.image_size, self.image_size, 1)
        elif len(image.shape) == 3:
            image = image.reshape(1, *image.shape, 1)
        
        # Предсказание
        prediction = self.model.predict(image, verbose=0)[0]
        predicted_class = np.argmax(prediction)
        confidence = float(prediction[predicted_class])
        
        # Маппинг классов
        class_names = ['bearish', 'neutral', 'bullish']
        pattern = class_names[predicted_class]
        
        return pattern, confidence
    
    def detect_patterns_batch(self, images: np.ndarray) -> Tuple[List[str], List[float]]:
        """
        Детекция паттернов для батча изображений
        
        Args:
            images: Батч изображений
            
        Returns:
            patterns: Список названий паттернов
            confidences: Список уверенностей
        """
        if not self.is_trained or self.model is None:
            logger.warning("Модель не обучена")
            return ["neutral"] * len(images), [0.0] * len(images)
        
        # Подготовка изображений
        if len(images.shape) == 3:
            images = images.reshape(-1, self.image_size, self.image_size, 1)
        
        # Предсказания
        predictions = self.model.predict(images, verbose=0)
        predicted_classes = np.argmax(predictions, axis=1)
        confidences = [float(predictions[i][predicted_classes[i]]) for i in range(len(predictions))]
        
        # Маппинг классов
        class_names = ['bearish', 'neutral', 'bullish']
        patterns = [class_names[cls] for cls in predicted_classes]
        
        return patterns, confidences
    
    def analyze_ohlcv_patterns(self, ohlcv_data: pd.DataFrame, window_size: int = 20) -> Dict:
        """
        Анализ паттернов в OHLCV данных
        
        Args:
            ohlcv_data: DataFrame с OHLCV данными
            window_size: Размер окна для анализа
            
        Returns:
            Результаты анализа паттернов
        """
        if len(ohlcv_data) < window_size:
            return {'error': 'Недостаточно данных для анализа'}
        
        # Берем последнее окно данных
        recent_data = ohlcv_data.tail(window_size)
        
        # Создаем изображение
        image = self._create_candlestick_image(recent_data)
        
        # Детекция паттерна
        pattern, confidence = self.detect_patterns(image)
        
        # Дополнительный анализ
        last_candle = ohlcv_data.iloc[-1]
        candle_type = 'bullish' if last_candle['close'] > last_candle['open'] else 'bearish'
        
        # Расчет силы тренда
        price_change = (ohlcv_data['close'].iloc[-1] - ohlcv_data['close'].iloc[-window_size]) / ohlcv_data['close'].iloc[-window_size]
        trend_strength = abs(price_change)
        
        return {
            'pattern': pattern,
            'confidence': confidence,
            'last_candle_type': candle_type,
            'price_change_percent': price_change * 100,
            'trend_strength': trend_strength,
            'window_size': window_size,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def save_model(self):
        """Сохранение модели"""
        if self.model is not None:
            model_file = os.path.join(self.model_path, "cnn_model.h5")
            
            self.model.save(model_file)
            
            # Сохраняем метаданные
            metadata = {
                'image_size': self.image_size,
                'is_trained': self.is_trained,
                'pattern_classes': self.pattern_classes,
                'saved_at': datetime.now().isoformat()
            }
            metadata_file = os.path.join(self.model_path, "metadata.pkl")
            joblib.dump(metadata, metadata_file)
            
            logger.info(f"CNN модель сохранена в {self.model_path}")
    
    def load_model(self) -> bool:
        """
        Загрузка сохраненной модели
        
        Returns:
            True если модель успешно загружена
        """
        try:
            from tensorflow.keras.models import load_model
            
            model_file = os.path.join(self.model_path, "cnn_model.h5")
            metadata_file = os.path.join(self.model_path, "metadata.pkl")
            
            if os.path.exists(model_file) and os.path.exists(metadata_file):
                self.model = load_model(model_file)
                metadata = joblib.load(metadata_file)
                
                self.image_size = metadata['image_size']
                self.is_trained = metadata['is_trained']
                self.pattern_classes = metadata['pattern_classes']
                
                logger.info(f"CNN модель загружена из {self.model_path}")
                return True
            else:
                logger.warning("Файлы CNN модели не найдены")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка загрузки CNN модели: {e}")
            return False
    
    def get_model_info(self) -> dict:
        """Получение информации о модели"""
        return {
            'image_size': self.image_size,
            'is_trained': self.is_trained,
            'pattern_classes': self.pattern_classes,
            'model_path': self.model_path,
            'model_exists': self.model is not None
        }
    
    def evaluate_model(self, images: np.ndarray, labels: np.ndarray) -> dict:
        """
        Оценка качества модели на тестовых данных
        
        Args:
            images: Тестовые изображения
            labels: Тестовые метки
            
        Returns:
            Метрики качества модели
        """
        if not self.is_trained or self.model is None:
            return {'error': 'Модель не обучена'}
        
        # Подготовка данных
        images = images.reshape(-1, self.image_size, self.image_size, 1)
        
        # Предсказания
        predictions = self.model.predict(images, verbose=0)
        predicted_classes = np.argmax(predictions, axis=1)
        
        # Метрики
        accuracy = accuracy_score(labels, predicted_classes)
        
        # Дополнительные метрики
        from sklearn.metrics import precision_score, recall_score, f1_score
        
        precision = precision_score(labels, predicted_classes, average='weighted', zero_division=0)
        recall = recall_score(labels, predicted_classes, average='weighted', zero_division=0)
        f1 = f1_score(labels, predicted_classes, average='weighted', zero_division=0)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'test_samples': len(images),
            'num_classes': len(np.unique(labels))
        } 