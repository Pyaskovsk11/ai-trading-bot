# Техническое Задание (ТЗ) для Разработчика: Улучшение AI Трейдинг-Бота в Cursor AI Cloud 4 Sonnet

**Версия:** 1.0
**Дата:** 28 мая 2025 г.

## 1. Введение

### 1.1 Цель Документа

Данное техническое задание (ТЗ) предназначено для разработчика, использующего среду Cursor AI Cloud 4 Sonnet, и описывает задачи по улучшению существующего AI трейдинг-бота. Цель улучшений — повысить адаптивность бота к рыночным условиям, улучшить качество торговых сигналов и внедрить более продвинутые механизмы управления риском.

### 1.2 Контекст Проекта

*   **Среда разработки:** Cursor AI Cloud 4 Sonnet
*   **Основные технологии:** Python, FastAPI, PostgreSQL, Docker Compose, PyTorch (или другая ML-библиотека)
*   **Существующая архитектура:** Предполагается наличие бэкенда на FastAPI, базы данных PostgreSQL, AI-модуля для генерации сигналов, интеграции с биржей (например, BingX) и Telegram-бота.
*   **Цель бота:** Торговля фьючерсами (BTC, ETH и другие альткоины) на основе технического анализа, новостей и AI-прогнозов.

### 1.3 Обзор Улучшений

1.  **Интеграция анализа доминации Bitcoin (BTC.D):** Добавление модуля для анализа BTC.D, определения рыночных режимов (альтсезон, доминирование BTC, нейтральный) и адаптации стратегии.
2.  **Реализация динамических стоп-лоссов (SL) и тейк-профитов (TP):** Внедрение адаптивных механизмов управления риском на основе волатильности (ATR) и структуры рынка.
3.  **Улучшение AI-модели для генерации сигналов:** Использование более продвинутых признаков (feature engineering), ансамблей моделей и фильтров для повышения точности сигналов.

## 2. Требования к Реализации

### 2.1 Общие Требования

*   **Язык программирования:** Python 3.9+
*   **Стиль кода:** Следовать PEP 8, использовать аннотации типов (type hinting).
*   **Управление зависимостями:** Использовать `requirements.txt` или `pyproject.toml`.
*   **Логирование:** Настроить подробное логирование всех ключевых операций, ошибок и решений бота.
*   **Конфигурация:** Все настраиваемые параметры (пороги, множители, API-ключи) должны выноситься в конфигурационные файлы или переменные окружения.
*   **Тестирование:** Покрыть новый код юнит-тестами (pytest) и интеграционными тестами.
*   **Документация:** Добавить docstrings к новым классам и функциям, обновить общую документацию проекта (README.md).

### 2.2 Модуль Анализа BTC.D и Режимов Рынка

**Задача:** Создать отдельный модуль (`market_regime_analyzer.py`) для анализа BTC.D и определения текущего рыночного режима.

**Компоненты:**

1.  **Класс `BTCDominanceAnalyzer`:**
    *   **Источник данных:** Получение данных BTC.D (например, с TradingView, CoinMarketCap API, или другого надежного источника). Реализовать интерфейс `DataProvider` для гибкости.
    *   **Методы:**
        *   `update_data(timeframes)`: Загрузка/обновление данных BTC.D для указанных таймфреймов (1d, 4h, 1h).
        *   `calculate_technical_indicators()`: Расчет EMA, RSI, MACD, ATR для данных BTC.D.
        *   `detect_patterns()`: Реализация детектора паттернов (как минимум "восходящий клин", "пробой уровня"). Использовать библиотеки, такие как `pandas_ta` или `talib` для индикаторов, и кастомную логику для паттернов.
        *   `identify_support_resistance()`: Определение статических и динамических уровней поддержки/сопротивления.
        *   `calculate_altcoin_strength(top_alts)`: Расчет индекса силы альткоинов (0-100) на основе анализа пар ALT/BTC.
        *   `get_market_regime()`: Определение текущего режима (`'btc_dominance'`, `'alt_season'`, `'neutral'`) на основе паттернов, уровней и индекса силы альткоинов. Хранить предыдущий режим для отслеживания изменений.
        *   `generate_btcd_features()`: Генерация словаря признаков на основе анализа BTC.D для передачи в основную AI-модель.
    *   **Хранение данных:** Кэширование данных BTC.D для избежания частых запросов к API.

2.  **Интеграция:**
    *   Модуль должен быть легко импортируемым и используемым другими частями системы (AI-модель, риск-менеджер, Telegram-бот).
    *   Предусмотреть обработку ошибок при получении данных или расчетах.

**Пример структуры (`market_regime_analyzer.py`):**

```python
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
# ... другие импорты

class DataProviderInterface:
    def get_btc_dominance(self, timeframe: str, limit: int = 1000) -> pd.DataFrame:
        raise NotImplementedError
    def get_pair_data(self, pair: str, timeframe: str, limit: int = 1000) -> pd.DataFrame:
        raise NotImplementedError
    # ... другие методы для получения данных

class BTCDominanceAnalyzer:
    def __init__(self, data_provider: DataProviderInterface, timeframes=["1d", "4h", "1h"]):
        self.data_provider = data_provider
        self.timeframes = timeframes
        self.btcd_data = {}
        self.patterns = {}
        self.support_resistance_levels = {
            "major": [57.0, 62.0, 65.0, 70.0], # Пример
            "dynamic": []
        }
        self.market_regime = "neutral"
        self.previous_regime = "neutral"
        self.last_update_time = None
        self.cache_duration = timedelta(minutes=30) # Кэшировать на 30 минут

    def _update_if_needed(self):
        """Обновляет данные, если кэш устарел"""
        now = datetime.now()
        if self.last_update_time is None or (now - self.last_update_time) > self.cache_duration:
            print("Updating BTCD data...")
            self.update_data()
            self.calculate_technical_indicators()
            self.detect_patterns()
            self.identify_support_resistance()
            self.last_update_time = now

    def update_data(self):
        # ... реализация загрузки данных ...
        pass

    def calculate_technical_indicators(self):
        # ... реализация расчета индикаторов ...
        pass

    def detect_patterns(self):
        # ... реализация детектора паттернов ...
        pass

    def identify_support_resistance(self):
        # ... реализация определения уровней ...
        pass

    def calculate_altcoin_strength(self, top_alts=["ETH", "SOL", "BNB"]):
        # ... реализация расчета индекса силы альткоинов ...
        return 50.0 # Placeholder

    def get_market_regime(self) -> str:
        self._update_if_needed()
        # ... логика определения режима на основе self.patterns, self.btcd_data, alt_strength ...
        alt_strength = self.calculate_altcoin_strength()
        # Пример простой логики:
        if self.patterns.get("1d", {}).get("rising_wedge") and self.patterns.get("1d", {}).get("breakdown"):
             self.market_regime = "alt_season"
        elif alt_strength > 70:
             self.market_regime = "alt_season"
        elif alt_strength < 30:
             self.market_regime = "btc_dominance"
        else:
             self.market_regime = "neutral"
        
        if self.market_regime != self.previous_regime:
            print(f"Market regime changed: {self.previous_regime} -> {self.market_regime}")
            self.previous_regime = self.market_regime
            
        return self.market_regime

    def generate_btcd_features(self) -> dict:
        self._update_if_needed()
        # ... реализация генерации признаков ...
        features = {
            "btcd_current": self.btcd_data.get("1d", pd.DataFrame({"close": [0]}))["close"].iloc[-1],
            "altcoin_strength_index": self.calculate_altcoin_strength() / 100.0,
            # ... другие признаки
        }
        return features

    # Вспомогательные приватные методы для паттернов, уровней и т.д.
    # def _detect_rising_wedge(self, data):
    # def _find_significant_levels(self, series, is_max):
    # ...
```

### 2.3 Динамические Стоп-Лоссы (SL) и Тейк-Профиты (TP)

**Задача:** Создать модуль (`dynamic_risk_manager.py`) для расчета динамических уровней SL и TP.

**Компоненты:**

1.  **Класс `DynamicRiskManager`:**
    *   **Зависимости:** Может использовать `BTCDominanceAnalyzer` для адаптации к режиму рынка.
    *   **Методы:**
        *   `calculate_atr_stop_loss(asset_data, entry_price, is_long, atr_multiplier)`: Расчет SL на основе ATR.
        *   `calculate_structure_stop_loss(asset_data, entry_price, is_long, lookback_period, buffer_percentage)`: Расчет SL на основе недавних минимумов/максимумов.
        *   `calculate_trailing_stop(current_price, current_trailing_stop, asset_data, is_long, method='atr', atr_multiplier=3.0)`: Расчет трейлинг-стопа (поддерживать разные методы).
        *   `calculate_take_profit_levels(entry_price, stop_loss_price, is_long, rr_ratios={'tp1': 1.5, 'tp2': 3.0}, method='rr')`: Расчет уровней TP (на основе R:R, можно добавить структурные уровни).
        *   `get_adaptive_stop_loss(asset, asset_data, entry_price, is_long, market_regime)`: Выбор и расчет оптимального SL с учетом режима рынка (например, шире стопы для альтов в альтсезон).
        *   `get_adaptive_take_profit(asset, entry_price, stop_loss_price, is_long, market_regime)`: Расчет адаптивных уровней TP.

2.  **Интеграция:**
    *   Модуль должен использоваться компонентом управления ордерами для установки и обновления SL/TP на бирже.
    *   Предусмотреть возможность частичного закрытия позиций на разных уровнях TP.

**Пример структуры (`dynamic_risk_manager.py`):**

```python
import pandas as pd
import pandas_ta as ta
# from market_regime_analyzer import BTCDominanceAnalyzer # Опционально

class DynamicRiskManager:
    # def __init__(self, btcd_analyzer: BTCDominanceAnalyzer = None):
    #     self.btcd_analyzer = btcd_analyzer

    def calculate_atr(self, asset_data: pd.DataFrame, length: int = 14) -> float:
        """Рассчитывает последнее значение ATR"""
        if 'high' not in asset_data or 'low' not in asset_data or 'close' not in asset_data:
            raise ValueError("DataFrame must contain 'high', 'low', 'close' columns")
        if len(asset_data) < length:
            return 0.0 # Недостаточно данных
        atr = ta.atr(asset_data['high'], asset_data['low'], asset_data['close'], length=length)
        return atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0.0

    def calculate_atr_stop_loss(self, asset_data: pd.DataFrame, entry_price: float, is_long: bool, atr_multiplier: float = 2.5, atr_length: int = 14) -> float:
        """Рассчитывает SL на основе ATR"""
        current_atr = self.calculate_atr(asset_data, length=atr_length)
        if current_atr == 0.0:
             # Fallback: использовать % от цены, если ATR недоступен
             stop_distance = entry_price * 0.02 # Пример: 2% стоп
        else:
             stop_distance = atr_multiplier * current_atr
             
        stop_loss_price = entry_price - stop_distance if is_long else entry_price + stop_distance
        return stop_loss_price

    def calculate_structure_stop_loss(self, asset_data: pd.DataFrame, entry_price: float, is_long: bool, lookback_period: int = 20, buffer_percentage: float = 0.001) -> float:
        """Рассчитывает SL на основе недавних экстремумов"""
        if len(asset_data) < lookback_period:
            # Fallback к ATR или % стопу
            return self.calculate_atr_stop_loss(asset_data, entry_price, is_long)
            
        relevant_data = asset_data.tail(lookback_period)
        buffer = entry_price * buffer_percentage

        if is_long:
            support_level = relevant_data['low'].min()
            stop_loss_price = support_level - buffer
        else:
            resistance_level = relevant_data['high'].max()
            stop_loss_price = resistance_level + buffer
            
        # Убедиться, что стоп не слишком близко
        min_stop_distance = entry_price * 0.005 # Минимум 0.5%
        if is_long and (entry_price - stop_loss_price) < min_stop_distance:
             stop_loss_price = entry_price - min_stop_distance
        elif not is_long and (stop_loss_price - entry_price) < min_stop_distance:
             stop_loss_price = entry_price + min_stop_distance
             
        return stop_loss_price

    def calculate_trailing_stop(self, current_price: float, current_trailing_stop: float, asset_data: pd.DataFrame, is_long: bool, method: str = 'atr', atr_multiplier: float = 3.0, atr_length: int = 14) -> float:
        """Рассчитывает новый уровень трейлинг-стопа"""
        if method == 'atr':
            current_atr = self.calculate_atr(asset_data, length=atr_length)
            if current_atr == 0.0: return current_trailing_stop # Не двигать стоп, если ATR=0
            stop_distance = atr_multiplier * current_atr
            potential_new_stop = current_price - stop_distance if is_long else current_price + stop_distance
        # Добавить другие методы (MA, Parabolic SAR, ...)    
        else:
            raise ValueError(f"Unsupported trailing stop method: {method}")

        if is_long:
            # Стоп двигается только вверх
            new_trailing_stop = max(current_trailing_stop, potential_new_stop)
        else:
            # Стоп двигается только вниз
            new_trailing_stop = min(current_trailing_stop, potential_new_stop)
            
        return new_trailing_stop

    def calculate_take_profit_levels(self, entry_price: float, stop_loss_price: float, is_long: bool, rr_ratios: dict = {"tp1": 1.5, "tp2": 3.0}) -> dict:
        """Рассчитывает уровни TP на основе R:R"""
        risk_per_unit = abs(entry_price - stop_loss_price)
        if risk_per_unit == 0: return {} # Избежать деления на ноль
        
        take_profit_levels = {}
        for level, ratio in rr_ratios.items():
            profit_target = risk_per_unit * ratio
            tp_price = entry_price + profit_target if is_long else entry_price - profit_target
            take_profit_levels[level] = tp_price
            
        return take_profit_levels

    # --- Адаптивные методы (пример) ---
    def get_adaptive_stop_loss(self, asset: str, asset_data: pd.DataFrame, entry_price: float, is_long: bool, market_regime: str) -> float:
        """Выбирает и рассчитывает адаптивный SL"""
        is_bitcoin = asset.upper() == 'BTC'
        atr_multiplier = 2.5
        
        # Пример адаптации множителя ATR
        if market_regime == 'alt_season' and not is_bitcoin:
            atr_multiplier = 3.0 # Шире стоп для альтов
        elif market_regime == 'btc_dominance' and not is_bitcoin:
            atr_multiplier = 2.0 # Уже стоп для альтов
            
        # Можно добавить логику выбора между ATR и структурным стопом
        return self.calculate_atr_stop_loss(asset_data, entry_price, is_long, atr_multiplier)

    def get_adaptive_take_profit(self, asset: str, entry_price: float, stop_loss_price: float, is_long: bool, market_regime: str) -> dict:
        """Рассчитывает адаптивные уровни TP"""
        is_bitcoin = asset.upper() == 'BTC'
        base_rr_ratios = {"tp1": 1.5, "tp2": 3.0}
        
        # Пример адаптации R:R
        if market_regime == 'alt_season' and not is_bitcoin:
             rr_ratios = {k: v * 1.3 for k, v in base_rr_ratios.items()} # Большие цели для альтов
        elif market_regime == 'btc_dominance' and is_bitcoin:
             rr_ratios = {k: v * 1.2 for k, v in base_rr_ratios.items()} # Большие цели для BTC
        else:
             rr_ratios = base_rr_ratios
             
        return self.calculate_take_profit_levels(entry_price, stop_loss_price, is_long, rr_ratios)
```

### 2.4 Улучшение AI-Модели и Сигналов

**Задача:** Улучшить существующий AI-модуль (`ai_predictor.py` или аналогичный) для генерации более точных сигналов.

**Компоненты:**

1.  **Feature Engineering:**
    *   Добавить признаки из модуля `BTCDominanceAnalyzer` (`generate_btcd_features()`).
    *   Реализовать расчет продвинутых технических индикаторов и признаков для торгуемых активов (например, данные стакана, если доступны, ставка финансирования, открытый интерес, продвинутые модели волатильности GARCH, скользящие корреляции).
    *   Создать класс `FeatureExtractor` для инкапсуляции логики извлечения признаков.

2.  **Моделирование:**
    *   Экспериментировать с ансамблями моделей (стэкинг, блендинг) для комбинирования прогнозов от разных базовых моделей (LSTM, CNN, Transformer, Gradient Boosting и т.д.).
    *   Рассмотреть использование моделей, специфичных для разных режимов рынка.
    *   Модель должна возвращать не только направление, но и вероятность/уверенность прогноза.

3.  **Фильтрация Сигналов:**
    *   Реализовать класс `SignalFilter`.
    *   Применять строгие правила конфлюенции: требовать подтверждения сигнала от нескольких индикаторов/моделей и на разных таймфреймах.
    *   Использовать `BTCDominanceAnalyzer` для адаптации порогов входа в зависимости от режима рынка (см. `AdaptiveEntryExitRules` в предыдущем документе).

**Пример структуры (`ai_predictor.py`):**

```python
import pandas as pd
# from market_regime_analyzer import BTCDominanceAnalyzer
# from feature_extractor import FeatureExtractor
# from signal_filter import SignalFilter
# ... импорты ML библиотек (sklearn, tensorflow, pytorch)

class AIPredictor:
    def __init__(self, model_path: str, feature_extractor, signal_filter, btcd_analyzer):
        self.model = self._load_model(model_path) # Загрузка обученной модели (или ансамбля)
        self.feature_extractor = feature_extractor
        self.signal_filter = signal_filter
        self.btcd_analyzer = btcd_analyzer

    def _load_model(self, path):
        # ... логика загрузки модели (например, joblib, tf.keras.models.load_model) ...
        pass

    def generate_signal(self, asset: str, asset_data: pd.DataFrame) -> dict | None:
        """Генерирует торговый сигнал для указанного актива"""
        # 1. Получить режим рынка и признаки BTC.D
        market_regime = self.btcd_analyzer.get_market_regime()
        btcd_features = self.btcd_analyzer.generate_btcd_features()
        
        # 2. Извлечь признаки для актива
        asset_features = self.feature_extractor.extract_features(asset_data)
        
        # 3. Объединить признаки
        all_features = {**asset_features, **btcd_features}
        # Добавить информацию о режиме рынка как признак
        all_features['market_regime_alt_season'] = 1 if market_regime == 'alt_season' else 0
        # ... и т.д.
        
        # 4. Сделать прогноз с помощью модели
        # Убедиться, что признаки подаются в модель в правильном формате и порядке
        prepared_features = self._prepare_features_for_model(all_features)
        prediction_output = self.model.predict(prepared_features) # Пример
        
        # 5. Интерпретировать выход модели
        prediction = self._interpret_prediction(prediction_output)
        # prediction = {'direction': 'long'/'short'/'neutral', 'probability': 0.75, 'confidence': 0.8}
        
        # 6. Отфильтровать сигнал
        signal = self.signal_filter.filter_signal(asset, prediction, asset_data, market_regime)
        # signal = {'asset': asset, 'direction': 'long', 'entry_price': ..., 'confidence': ..., 'reason': ...} или None
        
        return signal

    def _prepare_features_for_model(self, features: dict):
        # ... конвертация словаря признаков в формат, ожидаемый моделью (например, numpy array, DataFrame) ...
        pass

    def _interpret_prediction(self, model_output) -> dict:
        # ... интерпретация выхода модели в стандартизированный формат ...
        pass
```

### 2.5 Интеграция Компонентов

**Задача:** Обеспечить взаимодействие новых и существующих модулей.

1.  **Основной Цикл Бота (`main.py` или `trading_bot.py`):**
    *   Инициализировать `BTCDominanceAnalyzer`, `DynamicRiskManager`, `AIPredictor`.
    *   Периодически вызывать `AIPredictor.generate_signal()` для отслеживаемых активов.
    *   При получении сигнала: 
        *   Рассчитать размер позиции (`PositionSizer.calculate_size`).
        *   Рассчитать SL и TP (`DynamicRiskManager.get_adaptive_stop_loss`, `get_adaptive_take_profit`).
        *   Разместить ордер на бирже (`ExchangeAPIWrapper.place_order`).
    *   Реализовать логику управления открытыми позициями (обновление трейлинг-стопов, проверка TP).

2.  **Управление Ордерами (`order_manager.py`):**
    *   Взаимодействовать с `DynamicRiskManager` для получения уровней SL/TP.
    *   Взаимодействовать с API биржи для размещения и обновления ордеров (включая трейлинг-стопы, если поддерживаются биржей нативно, или эмулировать их).

3.  **Telegram-Бот (`telegram_interface.py`):**
    *   Интегрировать `BTCDominanceAnalyzer` для предоставления информации о BTC.D и режиме рынка по командам `/btcd`, `/altseason`, `/regime`.
    *   Реализовать систему отправки алертов о смене режима рынка или обнаружении паттернов BTC.D.

### 2.6 База Данных (PostgreSQL)

*   **Схемы:**
    *   Добавить таблицу для хранения исторических данных BTC.D.
    *   Добавить таблицу для хранения истории рыночных режимов.
    *   Расширить таблицу сделок (`trades`) для хранения информации о методе расчета SL/TP, режиме рынка на момент входа.
*   **Использование:** Сохранять результаты анализа, прогнозы и сделки для последующего анализа и отчетности.

## 3. Тестирование

*   **Юнит-тесты:** Покрыть все новые классы и их методы тестами (расчеты индикаторов, определение режимов, расчет SL/TP, генерация признаков).
*   **Интеграционные тесты:** Проверить взаимодействие между модулями (AI -> RiskManager -> OrderManager).
*   **Бэктестинг:** Создать или адаптировать существующий фреймворк для бэктестинга. Протестировать всю стратегию (включая анализ BTC.D и динамический риск-менеджмент) на длительном историческом периоде, охватывающем разные рыночные фазы. Оценить ключевые метрики (прибыльность, просадка, Sharpe Ratio, Sortino Ratio).

## 4. Развертывание (Docker Compose)

*   Обновить `docker-compose.yml`, если добавлены новые сервисы или зависимости.
*   Убедиться, что все необходимые переменные окружения (API-ключи, параметры конфигурации) передаются в контейнеры.
*   Протестировать запуск и работу всей системы в Docker-окружении.

## 5. План Работ (Примерный)

1.  **Неделя 1:**
    *   Настройка сбора данных BTC.D и сохранение в PostgreSQL.
    *   Реализация базового `BTCDominanceAnalyzer` (расчет индикаторов, определение уровней).
    *   Написание юнит-тестов для `BTCDominanceAnalyzer`.
2.  **Неделя 2:**
    *   Реализация детектора паттернов BTC.D и расчета индекса силы альткоинов.
    *   Реализация логики определения рыночного режима.
    *   Интеграция `BTCDominanceAnalyzer` с Telegram-ботом (команды /btcd, /regime, /altseason).
3.  **Неделя 3:**
    *   Реализация `DynamicRiskManager` (расчет ATR SL, структурного SL, R:R TP).
    *   Реализация трейлинг-стопов.
    *   Написание юнит-тестов для `DynamicRiskManager`.
4.  **Неделя 4:**
    *   Реализация адаптивных методов в `DynamicRiskManager` (использование `market_regime`).
    *   Интеграция `DynamicRiskManager` с модулем управления ордерами.
5.  **Неделя 5-6:**
    *   Реализация `FeatureExtractor` с новыми признаками (включая BTC.D).
    *   Обновление/переобучение AI-модели с новыми признаками.
    *   Реализация `SignalFilter` с адаптивными порогами.
    *   Интеграция обновленного `AIPredictor` в основной цикл бота.
6.  **Неделя 7-8:**
    *   Разработка/адаптация фреймворка для бэктестинга.
    *   Проведение комплексного бэктестинга.
    *   Оптимизация параметров стратегии.
    *   Интеграционное тестирование.
    *   Подготовка к развертыванию (обновление Docker, конфигурации).

## 6. Ожидаемые Результаты

*   Полностью функционирующий AI трейдинг-бот с интегрированным анализом BTC.D.
*   Адаптивная стратегия, переключающаяся между режимами рынка.
*   Использование динамических стоп-лоссов и тейк-профитов.
*   Улучшенная точность сигналов за счет продвинутых признаков и фильтров.
*   Подробная документация и тесты для нового функционала.
*   Отчет по результатам бэктестинга.
