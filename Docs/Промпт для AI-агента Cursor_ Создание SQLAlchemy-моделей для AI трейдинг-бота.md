# Промпт для AI-агента Cursor: Создание SQLAlchemy-моделей для AI трейдинг-бота

## Задача

Создать файл `app/db/models.py` с SQLAlchemy-моделями для таблиц базы данных PostgreSQL, необходимых для AI трейдинг-бота. Модели должны включать все необходимые связи, индексы и настройки для оптимальной работы с данными.

## Структура моделей

### Базовый класс и настройка метаданных

Создай базовый класс `Base` и настройку метаданных SQLAlchemy. Используй современный подход с `declarative_base()`. Добавь импорты всех необходимых модулей SQLAlchemy.

### Модель Users

Таблица для хранения пользователей с доступом к боту (whitelist).

**Поля:**
- `id`: Integer, первичный ключ, автоинкремент
- `telegram_id`: String(50), уникальный, индексированный
- `username`: String(100), может быть NULL
- `email`: String(255), может быть NULL
- `whitelist_status`: Boolean, по умолчанию False
- `created_at`: DateTime, по умолчанию текущее время
- `last_active`: DateTime, может быть NULL
- `settings`: JSONB, для хранения пользовательских настроек (используй PostgreSQL JSONB)

**Индексы:**
- По полю `telegram_id` для быстрого поиска пользователя
- По полю `whitelist_status` для фильтрации пользователей с доступом

### Модель XAI_Explanations

Таблица для хранения объяснений, генерируемых XAI-модулем.

**Поля:**
- `id`: Integer, первичный ключ, автоинкремент
- `explanation_text`: Text, текст объяснения
- `factors_used`: JSONB, факторы, использованные для генерации объяснения
- `created_at`: DateTime, по умолчанию текущее время
- `model_version`: String(50), версия модели XAI, использованной для генерации

**Индексы:**
- По полю `created_at` для сортировки по времени создания

### Модель Signals

Таблица для хранения торговых сигналов.

**Поля:**
- `id`: Integer, первичный ключ, автоинкремент
- `asset_pair`: String(20), пара активов (например, "BTC/USDT")
- `signal_type`: String(10), тип сигнала ("BUY", "SELL", "HOLD")
- `confidence_score`: Float, оценка уверенности от 0 до 1
- `price_at_signal`: Float, цена актива на момент сигнала
- `target_price`: Float, целевая цена
- `stop_loss`: Float, уровень стоп-лосс
- `time_frame`: String(10), временной фрейм анализа
- `created_at`: DateTime, по умолчанию текущее время
- `expires_at`: DateTime, время истечения сигнала
- `status`: String(20), статус сигнала ("ACTIVE", "EXPIRED", "TRIGGERED", "CANCELLED")
- `technical_indicators`: JSONB, значения технических индикаторов
- `xai_explanation_id`: Integer, внешний ключ к XAI_Explanations
- `smart_money_influence`: Float, оценка влияния крупных игроков от -1 до 1
- `volatility_estimate`: Float, оценка волатильности

**Связи:**
- Связь с `XAI_Explanations` (многие-к-одному): один XAI может объяснять несколько сигналов
- Настрой каскадное удаление: при удалении объяснения XAI связанные сигналы НЕ должны удаляться

**Индексы:**
- По полю `asset_pair` для быстрого поиска сигналов по активу
- По полю `created_at` для сортировки по времени создания
- По полю `status` для фильтрации активных сигналов
- По полю `signal_type` для фильтрации по типу сигнала

### Модель Trades

Таблица для хранения симулированных или реальных сделок на основе сигналов.

**Поля:**
- `id`: Integer, первичный ключ, автоинкремент
- `signal_id`: Integer, внешний ключ к Signals
- `user_id`: Integer, внешний ключ к Users (может быть NULL для системных сделок)
- `entry_price`: Float, цена входа
- `exit_price`: Float, цена выхода (может быть NULL для открытых позиций)
- `volume`: Float, объем сделки
- `pnl`: Float, прибыль/убыток (может быть NULL для открытых позиций)
- `pnl_percentage`: Float, процент прибыли/убытка
- `entry_time`: DateTime, время входа в позицию
- `exit_time`: DateTime, время выхода из позиции (может быть NULL)
- `status`: String(20), статус сделки ("OPEN", "CLOSED", "CANCELLED")
- `notes`: Text, заметки по сделке (может быть NULL)

**Связи:**
- Связь с `Signals` (многие-к-одному): один сигнал может привести к нескольким сделкам
- Связь с `Users` (многие-к-одному): один пользователь может иметь много сделок
- Настрой каскадное удаление: при удалении сигнала связанные сделки должны сохраняться (установи NULL)
- Настрой каскадное удаление: при удалении пользователя связанные сделки должны сохраняться (установи NULL)

**Индексы:**
- По полю `signal_id` для связи с сигналами
- По полю `user_id` для фильтрации сделок пользователя
- По полю `entry_time` для сортировки по времени входа
- По полю `status` для фильтрации открытых/закрытых сделок

### Модель News_Articles

Таблица для хранения новостей, анализируемых RAG-модулем.

**Поля:**
- `id`: Integer, первичный ключ, автоинкремент
- `title`: String(255), заголовок новости
- `content`: Text, содержание новости
- `source`: String(100), источник новости
- `published_at`: DateTime, время публикации
- `fetched_at`: DateTime, время получения ботом
- `sentiment_score`: Float, оценка настроения от -1 до 1
- `processed`: Boolean, флаг обработки RAG-модулем
- `url`: String(512), URL источника
- `affected_assets`: ARRAY(String), массив затронутых активов (используй PostgreSQL Array)

**Индексы:**
- По полю `published_at` для сортировки по времени публикации
- По полю `processed` для фильтрации необработанных новостей
- По полю `sentiment_score` для фильтрации по настроению

### Модель Signal_News_Relevance

Таблица для связи между сигналами и новостями (многие-ко-многим).

**Поля:**
- `id`: Integer, первичный ключ, автоинкремент
- `signal_id`: Integer, внешний ключ к Signals
- `news_id`: Integer, внешний ключ к News_Articles
- `relevance_score`: Float, оценка релевантности новости к сигналу от 0 до 1
- `impact_type`: String(20), тип влияния ("POSITIVE", "NEGATIVE", "NEUTRAL")

**Связи:**
- Связь с `Signals` (многие-к-одному)
- Связь с `News_Articles` (многие-к-одному)
- Настрой каскадное удаление: при удалении сигнала или новости связи должны удаляться

**Индексы:**
- По полю `signal_id` для быстрого поиска новостей, связанных с сигналом
- По полю `news_id` для быстрого поиска сигналов, связанных с новостью
- По полю `relevance_score` для сортировки по релевантности

## Дополнительные требования

1. Добавь методы `__repr__` для всех моделей для удобства отладки
2. Используй `relationship()` для определения связей между таблицами
3. Добавь проверки ограничений для числовых полей (например, confidence_score должен быть от 0 до 1)
4. Используй соответствующие типы данных PostgreSQL (JSONB для JSON-данных, ARRAY для массивов)
5. Добавь комментарии к полям и моделям для лучшей документации
6. Используй именованные ограничения для внешних ключей и индексов

## Пример структуры файла

```python
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, CheckConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Модель Users
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    # Остальные поля...
    
    # Связи
    trades = relationship("Trade", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id='{self.telegram_id}')>"

# Остальные модели...
```

Пожалуйста, реализуй все модели согласно описанию выше, с правильными связями, индексами и ограничениями.
