"""
ML Supercharged Ensemble - Ансамбль из 10 ML моделей для экстремальной точности
ЦЕЛЬ: Повышение точности предсказаний до 90%+ для достижения 100% доходности
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import asyncio
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
import xgboost as xgb
import lightgbm as lgb
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class MLSuperchargedEnsemble:
    """
    ML Суперчарджинг - Ансамбль из 10 моделей для экстремальной точности
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.model_weights = {}
        self.is_trained = False
        
        # Инициализируем все модели
        self._initialize_models()
        
        logger.info("ML Supercharged Ensemble инициализирован с 10 моделями")
    
    def _initialize_models(self):
        """Инициализация всех ML моделей"""
        
        # 1. Random Forest - Базовая модель
        self.models['random_forest'] = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        # 2. XGBoost - Градиентный бустинг
        self.models['xgboost'] = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=8,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        
        # 3. LightGBM - Быстрый градиентный бустинг
        self.models['lightgbm'] = lgb.LGBMClassifier(
            n_estimators=300,
            max_depth=8,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        
        # 4. Gradient Boosting - Классический бустинг
        self.models['gradient_boosting'] = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42
        )
        
        # 5. Neural Network - Многослойный перцептрон
        self.models['neural_network'] = MLPClassifier(
            hidden_layer_sizes=(100, 50, 25),
            activation='relu',
            solver='adam',
            alpha=0.001,
            learning_rate='adaptive',
            max_iter=500,
            random_state=42
        )
        
        # 6. Support Vector Machine - SVM
        self.models['svm'] = SVC(
            kernel='rbf',
            C=1.0,
            gamma='scale',
            probability=True,
            random_state=42
        )
        
        # 7. Logistic Regression - Логистическая регрессия
        self.models['logistic'] = LogisticRegression(
            C=1.0,
            solver='liblinear',
            random_state=42,
            max_iter=1000
        )
        
        # 8. Extra Trees - Экстремально рандомизированные деревья
        from sklearn.ensemble import ExtraTreesClassifier
        self.models['extra_trees'] = ExtraTreesClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        # 9. AdaBoost - Адаптивный бустинг
        from sklearn.ensemble import AdaBoostClassifier
        self.models['adaboost'] = AdaBoostClassifier(
            n_estimators=100,
            learning_rate=1.0,
            random_state=42
        )
        
        # 10. Voting Classifier - Голосующий классификатор
        from sklearn.ensemble import VotingClassifier
        base_models = [
            ('rf_vote', RandomForestClassifier(n_estimators=100, random_state=42)),
            ('xgb_vote', xgb.XGBClassifier(n_estimators=100, random_state=42)),
            ('lgb_vote', lgb.LGBMClassifier(n_estimators=100, random_state=42, verbose=-1))
        ]
        self.models['voting'] = VotingClassifier(
            estimators=base_models,
            voting='soft'
        )
        
        # Инициализируем скейлеры для каждой модели
        for model_name in self.models.keys():
            if model_name in ['neural_network', 'svm', 'logistic']:
                self.scalers[model_name] = StandardScaler()
            else:
                self.scalers[model_name] = RobustScaler()
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Подготовка признаков для ML моделей"""
        try:
            features = pd.DataFrame()
            
            # 1. Технические индикаторы
            features['rsi'] = data.get('rsi', 50)
            features['macd'] = data.get('macd', 0)
            features['macd_signal'] = data.get('macd_signal', 0)
            features['macd_histogram'] = data.get('macd_histogram', 0)
            features['bb_upper'] = data.get('bb_upper', 0)
            features['bb_lower'] = data.get('bb_lower', 0)
            features['bb_middle'] = data.get('bb_middle', 0)
            features['ema_12'] = data.get('ema_12', 0)
            features['ema_26'] = data.get('ema_26', 0)
            features['sma_50'] = data.get('sma_50', 0)
            features['sma_200'] = data.get('sma_200', 0)
            
            # 2. Ценовые признаки
            if 'close' in data.columns:
                features['price_change'] = data['close'].pct_change()
                features['price_volatility'] = data['close'].rolling(20).std()
                features['price_momentum'] = data['close'] / data['close'].shift(10) - 1
                
                # Высокие и низкие цены
                features['high_low_ratio'] = data.get('high', data['close']) / data.get('low', data['close'])
                features['close_high_ratio'] = data['close'] / data.get('high', data['close'])
                features['close_low_ratio'] = data['close'] / data.get('low', data['close'])
            
            # 3. Объемные признаки
            if 'volume' in data.columns:
                features['volume'] = data['volume']
                features['volume_sma'] = data['volume'].rolling(20).mean()
                features['volume_ratio'] = data['volume'] / features['volume_sma']
                features['volume_change'] = data['volume'].pct_change()
            else:
                features['volume'] = 1000000  # Дефолтное значение
                features['volume_sma'] = 1000000
                features['volume_ratio'] = 1.0
                features['volume_change'] = 0.0
            
            # 4. Лаговые признаки
            for lag in [1, 2, 3, 5, 10]:
                features[f'rsi_lag_{lag}'] = features['rsi'].shift(lag)
                features[f'macd_lag_{lag}'] = features['macd'].shift(lag)
                if 'close' in data.columns:
                    features[f'price_change_lag_{lag}'] = features['price_change'].shift(lag)
            
            # 5. Скользящие средние индикаторов
            features['rsi_sma_5'] = features['rsi'].rolling(5).mean()
            features['rsi_sma_10'] = features['rsi'].rolling(10).mean()
            features['macd_sma_5'] = features['macd'].rolling(5).mean()
            features['macd_sma_10'] = features['macd'].rolling(10).mean()
            
            # 6. Производные признаки
            features['rsi_momentum'] = features['rsi'] - features['rsi'].shift(5)
            features['macd_momentum'] = features['macd'] - features['macd'].shift(5)
            features['bb_position'] = (features['ema_12'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
            features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / features['bb_middle']
            
            # 7. Взаимодействия признаков
            features['rsi_macd_interaction'] = features['rsi'] * features['macd']
            features['price_volume_interaction'] = features.get('price_change', 0) * features['volume_ratio']
            
            # 8. Временные признаки
            if hasattr(data.index, 'hour'):
                features['hour'] = data.index.hour
                features['day_of_week'] = data.index.dayofweek
                features['is_weekend'] = (data.index.dayofweek >= 5).astype(int)
            else:
                features['hour'] = 12  # Дефолт
                features['day_of_week'] = 1
                features['is_weekend'] = 0
            
            # Заполняем NaN значения
            features = features.fillna(method='ffill').fillna(0)
            
            return features
            
        except Exception as e:
            logger.error(f"Ошибка подготовки признаков: {e}")
            # Возвращаем минимальный набор признаков
            return pd.DataFrame({
                'rsi': [50] * len(data),
                'macd': [0] * len(data),
                'volume_ratio': [1] * len(data),
                'price_change': [0] * len(data)
            })
    
    def create_labels(self, data: pd.DataFrame, future_periods: int = 5) -> pd.Series:
        """Создание меток для обучения"""
        try:
            if 'close' not in data.columns:
                return pd.Series([1] * len(data))  # Нейтральный класс
            
            # Рассчитываем будущую доходность
            future_returns = data['close'].shift(-future_periods) / data['close'] - 1
            
            # Создаем метки: 0 - падение >2%, 1 - нейтрально, 2 - рост >2%
            labels = pd.Series(1, index=data.index)  # Нейтральный класс по умолчанию
            labels[future_returns > 0.02] = 2   # Сильный рост -> класс 2
            labels[future_returns < -0.02] = 0  # Сильное падение -> класс 0
            
            return labels
            
        except Exception as e:
            logger.error(f"Ошибка создания меток: {e}")
            return pd.Series([0] * len(data))
    
    async def train_ensemble(self, historical_data: Dict[str, pd.DataFrame]) -> Dict:
        """Обучение ансамбля моделей"""
        try:
            logger.info("Начинаем обучение ML ансамбля...")
            
            # Объединяем данные всех символов
            all_features = []
            all_labels = []
            
            for symbol, data in historical_data.items():
                if len(data) < 100:  # Минимум данных для обучения
                    continue
                
                features = self.prepare_features(data)
                labels = self.create_labels(data)
                
                # Удаляем последние строки (нет будущих данных)
                features = features[:-10]
                labels = labels[:-10]
                
                all_features.append(features)
                all_labels.append(labels)
            
            if not all_features:
                logger.error("Нет данных для обучения")
                return {'success': False, 'error': 'Нет данных'}
            
            # Объединяем все данные
            X = pd.concat(all_features, ignore_index=True)
            y = pd.concat(all_labels, ignore_index=True)
            
            # Удаляем строки с NaN
            mask = ~(X.isna().any(axis=1) | y.isna())
            X = X[mask]
            y = y[mask]
            
            if len(X) < 100:
                logger.error("Недостаточно данных после очистки")
                return {'success': False, 'error': 'Недостаточно данных'}
            
            logger.info(f"Обучаем на {len(X)} образцах с {len(X.columns)} признаками")
            
            # Обучаем каждую модель
            model_scores = {}
            
            for model_name, model in self.models.items():
                try:
                    logger.info(f"Обучаем модель: {model_name}")
                    
                    # Масштабируем данные если нужно
                    if model_name in self.scalers:
                        X_scaled = self.scalers[model_name].fit_transform(X)
                    else:
                        X_scaled = X.values
                    
                    # Обучаем модель
                    model.fit(X_scaled, y)
                    
                    # Оцениваем качество
                    y_pred = model.predict(X_scaled)
                    accuracy = accuracy_score(y, y_pred)
                    
                    model_scores[model_name] = accuracy
                    logger.info(f"Модель {model_name}: точность {accuracy:.3f}")
                    
                except Exception as e:
                    logger.error(f"Ошибка обучения модели {model_name}: {e}")
                    model_scores[model_name] = 0.0
            
            # Рассчитываем веса моделей на основе их точности
            total_score = sum(model_scores.values())
            if total_score > 0:
                self.model_weights = {name: score/total_score for name, score in model_scores.items()}
            else:
                # Равные веса если все модели провалились
                self.model_weights = {name: 1.0/len(self.models) for name in self.models.keys()}
            
            self.is_trained = True
            
            # Сохраняем важность признаков
            self._calculate_feature_importance(X.columns)
            
            logger.info("Обучение ансамбля завершено успешно")
            
            return {
                'success': True,
                'model_scores': model_scores,
                'model_weights': self.model_weights,
                'feature_count': len(X.columns),
                'sample_count': len(X),
                'average_accuracy': np.mean(list(model_scores.values()))
            }
            
        except Exception as e:
            logger.error(f"Ошибка обучения ансамбля: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_feature_importance(self, feature_names: List[str]):
        """Расчет важности признаков"""
        try:
            importance_scores = {}
            
            for model_name, model in self.models.items():
                if hasattr(model, 'feature_importances_'):
                    importance_scores[model_name] = dict(zip(feature_names, model.feature_importances_))
                elif hasattr(model, 'coef_'):
                    importance_scores[model_name] = dict(zip(feature_names, np.abs(model.coef_[0])))
            
            # Усредняем важность по всем моделям
            if importance_scores:
                avg_importance = {}
                for feature in feature_names:
                    scores = [importance_scores[model].get(feature, 0) for model in importance_scores.keys()]
                    avg_importance[feature] = np.mean(scores)
                
                self.feature_importance = avg_importance
                
        except Exception as e:
            logger.error(f"Ошибка расчета важности признаков: {e}")
    
    async def predict_signal(self, current_data: pd.DataFrame) -> Dict:
        """Предсказание сигнала с помощью ансамбля"""
        try:
            if not self.is_trained:
                return {
                    'signal': 'hold',
                    'confidence': 0.0,
                    'reason': 'Модели не обучены'
                }
            
            # Подготавливаем признаки
            features = self.prepare_features(current_data)
            
            if len(features) == 0:
                return {
                    'signal': 'hold',
                    'confidence': 0.0,
                    'reason': 'Нет признаков'
                }
            
            # Берем последнюю строку
            X = features.iloc[-1:].fillna(0)
            
            # Получаем предсказания от всех моделей
            predictions = {}
            probabilities = {}
            
            for model_name, model in self.models.items():
                try:
                    # Масштабируем данные если нужно
                    if model_name in self.scalers:
                        X_scaled = self.scalers[model_name].transform(X)
                    else:
                        X_scaled = X.values
                    
                    # Предсказание
                    pred = model.predict(X_scaled)[0]
                    predictions[model_name] = pred
                    
                    # Вероятности если доступны
                    if hasattr(model, 'predict_proba'):
                        proba = model.predict_proba(X_scaled)[0]
                        probabilities[model_name] = proba
                    
                except Exception as e:
                    logger.error(f"Ошибка предсказания модели {model_name}: {e}")
                    predictions[model_name] = 0
                    probabilities[model_name] = [0.33, 0.34, 0.33]  # Нейтральные вероятности
            
            # Взвешенное голосование
            weighted_prediction = 0
            total_weight = 0
            
            for model_name, pred in predictions.items():
                weight = self.model_weights.get(model_name, 0)
                weighted_prediction += pred * weight
                total_weight += weight
            
            if total_weight > 0:
                final_prediction = weighted_prediction / total_weight
            else:
                final_prediction = 0
            
            # Определяем сигнал
            if final_prediction > 0.3:
                signal = 'buy'
            elif final_prediction < -0.3:
                signal = 'sell'
            else:
                signal = 'hold'
            
            # Рассчитываем уверенность
            confidence = abs(final_prediction)
            
            # Дополнительная проверка консенсуса
            buy_votes = sum(1 for pred in predictions.values() if pred > 0)
            sell_votes = sum(1 for pred in predictions.values() if pred < 0)
            total_votes = len(predictions)
            
            consensus = max(buy_votes, sell_votes) / total_votes if total_votes > 0 else 0
            
            # Корректируем уверенность на основе консенсуса
            confidence = confidence * consensus
            
            # Анализ важных признаков
            important_features = self._analyze_important_features(X)
            
            return {
                'signal': signal,
                'confidence': confidence,
                'final_prediction': final_prediction,
                'model_predictions': predictions,
                'consensus': consensus,
                'buy_votes': buy_votes,
                'sell_votes': sell_votes,
                'total_votes': total_votes,
                'important_features': important_features,
                'reason': f"ML Ансамбль: {signal} (уверенность: {confidence:.3f}, консенсус: {consensus:.3f})"
            }
            
        except Exception as e:
            logger.error(f"Ошибка предсказания ансамбля: {e}")
            return {
                'signal': 'hold',
                'confidence': 0.0,
                'reason': f'Ошибка: {str(e)}'
            }
    
    def _analyze_important_features(self, X: pd.DataFrame) -> Dict:
        """Анализ важных признаков для текущего предсказания"""
        try:
            if not self.feature_importance:
                return {}
            
            current_values = X.iloc[0].to_dict()
            
            # Топ-5 самых важных признаков
            top_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
            
            important_analysis = {}
            for feature, importance in top_features:
                if feature in current_values:
                    important_analysis[feature] = {
                        'value': current_values[feature],
                        'importance': importance,
                        'normalized_value': (current_values[feature] - 50) / 50 if 'rsi' in feature else current_values[feature]
                    }
            
            return important_analysis
            
        except Exception as e:
            logger.error(f"Ошибка анализа важных признаков: {e}")
            return {}
    
    def get_ensemble_stats(self) -> Dict:
        """Получение статистики ансамбля"""
        return {
            'is_trained': self.is_trained,
            'model_count': len(self.models),
            'model_names': list(self.models.keys()),
            'model_weights': self.model_weights,
            'top_features': sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:10] if self.feature_importance else [],
            'ensemble_type': 'Weighted Voting Ensemble',
            'target_accuracy': '90%+',
            'prediction_classes': ['sell (-1)', 'hold (0)', 'buy (1)']
        }
    
    async def retrain_if_needed(self, performance_metrics: Dict) -> bool:
        """Переобучение при снижении производительности"""
        try:
            if not performance_metrics:
                return False
            
            accuracy = performance_metrics.get('accuracy', 0)
            
            # Переобучаем если точность упала ниже 60%
            if accuracy < 0.6:
                logger.warning(f"Точность упала до {accuracy:.3f}, требуется переобучение")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка проверки необходимости переобучения: {e}")
            return False
    
    def save_ensemble(self, filepath: str):
        """Сохранение обученного ансамбля"""
        try:
            ensemble_data = {
                'models': self.models,
                'scalers': self.scalers,
                'model_weights': self.model_weights,
                'feature_importance': self.feature_importance,
                'is_trained': self.is_trained
            }
            
            joblib.dump(ensemble_data, filepath)
            logger.info(f"Ансамбль сохранен в {filepath}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения ансамбля: {e}")
    
    def load_ensemble(self, filepath: str):
        """Загрузка обученного ансамбля"""
        try:
            ensemble_data = joblib.load(filepath)
            
            self.models = ensemble_data['models']
            self.scalers = ensemble_data['scalers']
            self.model_weights = ensemble_data['model_weights']
            self.feature_importance = ensemble_data['feature_importance']
            self.is_trained = ensemble_data['is_trained']
            
            logger.info(f"Ансамбль загружен из {filepath}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки ансамбля: {e}")

# Глобальный экземпляр ML ансамбля
ml_ensemble = MLSuperchargedEnsemble() 