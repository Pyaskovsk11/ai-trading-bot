# Промпт для AI-агента Cursor: Создание гайда по тестированию AI трейдинг-бота

## Задача

Создать гайд по тестированию AI трейдинг-бота, который фокусируется на необходимом минимуме тестов для проверки правильности работы основных компонентов. Гайд должен использовать pytest в качестве основного фреймворка и включать примеры тестов для ключевых модулей.

## Структура гайда

### 1. Введение в тестирование проекта

Краткое введение, объясняющее:
- Важность тестирования для трейдинг-бота
- Общий подход к тестированию (от простого к сложному)
- Структуру тестов в проекте (папка `tests/` и её организация)
- Базовую настройку pytest для проекта

### 2. Настройка тестового окружения

Описание настройки тестового окружения, включая:
- Установку pytest и необходимых плагинов
- Создание файла `conftest.py` с общими фикстурами
- Настройку тестовой базы данных (SQLite в памяти для тестов)
- Создание моков для внешних API (BingX, Hector RAG)

### 3. Тестирование утилит и базовых функций

Примеры тестов для модуля `app/utils/indicators.py`:
- Тест для функции расчета RSI
- Тест для функции расчета MACD
- Тест для определения свечных моделей
- Обработка крайних случаев (недостаточно данных, некорректные входные данные)

### 4. Тестирование сервисов бизнес-логики

Примеры тестов для сервисов в `app/services/`:
- Тест для `technical_analysis_service.py`
- Тест для `signal_generation_service.py`
- Тест для `xai_service.py`
- Использование моков для изоляции тестируемого сервиса

### 5. Тестирование API эндпоинтов

Примеры тестов для API эндпоинтов в `app/api/`:
- Настройка TestClient для FastAPI
- Тест для эндпоинта получения сигналов
- Тест для эндпоинта создания пользователя
- Проверка валидации входных данных и обработки ошибок

### 6. Интеграционное тестирование

Примеры базовых интеграционных тестов:
- Тест полного цикла генерации сигнала
- Тест взаимодействия между сервисами
- Проверка сохранения данных в БД

### 7. Тестирование Telegram-бота

Базовые тесты для Telegram-бота:
- Тест обработки команд
- Тест форматирования сообщений
- Мокирование Telegram API

### 8. Рекомендации по запуску тестов

Инструкции по запуску тестов:
- Запуск всех тестов
- Запуск тестов для конкретного модуля
- Запуск тестов с маркерами
- Генерация отчета о покрытии кода тестами

## Примеры кода для гайда

### Пример настройки тестовой базы данных в `conftest.py`

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def test_engine():
    # Создаем SQLite в памяти для тестов
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="function")
def db_session(test_engine):
    # Создаем новую сессию для каждого теста
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    # Переопределяем зависимость get_db для использования тестовой сессии
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
```

### Пример теста для технического индикатора

```python
import pytest
import numpy as np
import pandas as pd
from app.utils.indicators import calculate_rsi

def test_calculate_rsi_normal_case():
    # Подготавливаем тестовые данные
    prices = pd.Series([10, 11, 10.5, 10.8, 11.2, 10.9, 11.5, 11.7, 12.0, 11.8, 12.1, 12.5, 12.3, 12.8])
    
    # Вызываем тестируемую функцию
    rsi = calculate_rsi(prices, period=14)
    
    # Проверяем результат
    assert rsi is not None
    assert 0 <= rsi <= 100
    # Можно добавить более точную проверку, если известно ожидаемое значение

def test_calculate_rsi_insufficient_data():
    # Тест с недостаточным количеством данных
    prices = pd.Series([10, 11, 10.5])
    
    # Вызываем тестируемую функцию
    rsi = calculate_rsi(prices, period=14)
    
    # Проверяем, что функция корректно обрабатывает недостаточное количество данных
    assert rsi is None

def test_calculate_rsi_empty_data():
    # Тест с пустыми данными
    prices = pd.Series([])
    
    # Вызываем тестируемую функцию
    rsi = calculate_rsi(prices, period=14)
    
    # Проверяем, что функция корректно обрабатывает пустые данные
    assert rsi is None
```

### Пример теста для сервиса генерации сигналов

```python
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app.services.signal_generation_service import generate_signal_for_asset
from app.db.models import Signal

@pytest.fixture
def mock_data():
    # Подготавливаем моки для зависимостей
    return {
        "prices": [100.0, 101.5, 102.3, 101.8, 103.2, 104.5, 103.8, 105.2],
        "technical_indicators": {
            "rsi": 65.5,
            "macd": 0.75,
            "ema_short": 104.2,
            "ema_long": 102.8
        },
        "news_sentiment": {
            "sentiment_score": 0.8,
            "affected_assets": ["BTC/USDT"],
            "summary": "Positive news about Bitcoin adoption"
        }
    }

@patch("app.services.data_collection_service.fetch_bingx_prices")
@patch("app.services.technical_analysis_service.analyze_technical_indicators")
@patch("app.services.rag_analysis_service.analyze_news_with_hector_rag")
def test_generate_signal_for_asset_buy_signal(
    mock_rag, mock_ta, mock_prices, mock_data, db_session
):
    # Настраиваем моки
    mock_prices.return_value = mock_data["prices"]
    mock_ta.return_value = mock_data["technical_indicators"]
    mock_rag.return_value = mock_data["news_sentiment"]
    
    # Вызываем тестируемую функцию
    signal = generate_signal_for_asset("BTC/USDT", db_session)
    
    # Проверяем результат
    assert signal is not None
    assert signal.asset_pair == "BTC/USDT"
    assert signal.signal_type == "BUY"  # Предполагаем, что с такими данными должен быть сигнал на покупку
    assert signal.confidence_score > 0.5
    assert signal.price_at_signal == mock_data["prices"][-1]
    assert signal.technical_indicators["rsi"] == mock_data["technical_indicators"]["rsi"]
    assert signal.xai_explanation_id is not None  # Проверяем, что было создано объяснение

@patch("app.services.data_collection_service.fetch_bingx_prices")
@patch("app.services.technical_analysis_service.analyze_technical_indicators")
@patch("app.services.rag_analysis_service.analyze_news_with_hector_rag")
def test_generate_signal_for_asset_no_signal(
    mock_rag, mock_ta, mock_prices, db_session
):
    # Настраиваем моки для случая, когда сигнал не должен генерироваться
    mock_prices.return_value = [100.0, 99.5, 99.8, 100.2, 99.7, 99.9, 100.1, 100.0]
    mock_ta.return_value = {
        "rsi": 50.2,  # Нейтральный RSI
        "macd": 0.05,  # Слабый MACD
        "ema_short": 100.0,
        "ema_long": 99.9
    }
    mock_rag.return_value = {
        "sentiment_score": 0.1,  # Нейтральные новости
        "affected_assets": ["BTC/USDT"],
        "summary": "No significant news about Bitcoin"
    }
    
    # Вызываем тестируемую функцию
    signal = generate_signal_for_asset("BTC/USDT", db_session)
    
    # Проверяем, что сигнал не был сгенерирован
    assert signal is None
```

### Пример теста для API эндпоинта

```python
def test_get_signals(client, db_session):
    # Подготавливаем тестовые данные
    # (здесь должен быть код для создания тестовых сигналов в БД)
    
    # Выполняем запрос к API
    response = client.get("/api/v1/signals/?limit=10")
    
    # Проверяем результат
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    
    # Проверяем структуру возвращаемых данных
    if data["items"]:
        signal = data["items"][0]
        assert "id" in signal
        assert "asset_pair" in signal
        assert "signal_type" in signal
        assert "confidence_score" in signal
        assert "created_at" in signal

def test_create_user(client):
    # Подготавливаем тестовые данные
    user_data = {
        "telegram_id": "12345678",
        "username": "test_user",
        "email": "test@example.com"
    }
    
    # Выполняем запрос к API
    response = client.post("/api/v1/users/", json=user_data)
    
    # Проверяем результат
    assert response.status_code == 201
    data = response.json()
    assert data["telegram_id"] == user_data["telegram_id"]
    assert data["username"] == user_data["username"]
    assert data["whitelist_status"] == False  # По умолчанию False
    
    # Проверяем, что нельзя создать пользователя с тем же telegram_id
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 400  # Bad Request
```

## Рекомендации по реализации

1. Начните с настройки тестового окружения и базовых фикстур
2. Реализуйте тесты для утилит и базовых функций
3. Переходите к тестированию сервисов бизнес-логики
4. Реализуйте тесты для API эндпоинтов
5. Добавьте базовые интеграционные тесты
6. Настройте тесты для Telegram-бота

Фокусируйтесь на проверке правильности работы ключевых компонентов и бизнес-логики, а не на 100% покрытии кода. Используйте моки для изоляции тестируемых компонентов от внешних зависимостей.

Пожалуйста, создайте гайд по тестированию, который будет понятен разработчикам с разным уровнем опыта и поможет убедиться, что AI трейдинг-бот работает правильно.
