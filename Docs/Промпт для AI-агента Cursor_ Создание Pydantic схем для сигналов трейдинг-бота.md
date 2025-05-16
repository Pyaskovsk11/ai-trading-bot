# Промпт для AI-агента Cursor: Создание Pydantic схем для сигналов трейдинг-бота

## Задача

Создать файл `app/schemas/signal.py` с Pydantic моделями для валидации данных API запросов и ответов, связанных с торговыми сигналами. Модели должны включать вложенные структуры для XAI объяснений и связанных новостей.

## Структура моделей

### Базовые импорты и настройки

Добавь все необходимые импорты для Pydantic и типов данных, включая:
- `BaseModel` из `pydantic`
- `Optional`, `List`, `Dict` из `typing`
- `datetime` из `datetime`
- `Field` из `pydantic` для валидации и документации полей
- `validator` из `pydantic` для кастомной валидации

### Вспомогательные модели для вложенных структур

#### XAIExplanationBase

Базовая модель для XAI объяснений.

**Поля:**
- `explanation_text`: str, текст объяснения
- `factors_used`: Dict[str, float], факторы, использованные для генерации объяснения и их веса
- `model_version`: Optional[str], версия модели XAI (опционально)

#### NewsBase

Базовая модель для новостных статей.

**Поля:**
- `title`: str, заголовок новости
- `source`: str, источник новости
- `published_at`: datetime, время публикации
- `sentiment_score`: float, оценка настроения от -1 до 1
- `url`: Optional[str], URL источника (опционально)

#### NewsRelevance

Модель для связи новости с сигналом и оценки релевантности.

**Поля:**
- `news`: NewsBase, данные новости
- `relevance_score`: float, оценка релевантности новости к сигналу от 0 до 1
- `impact_type`: str, тип влияния ("POSITIVE", "NEGATIVE", "NEUTRAL")

### Основные модели для сигналов

#### SignalBase

Базовая модель с общими полями для всех операций с сигналами.

**Поля:**
- `asset_pair`: str, пара активов (например, "BTC/USDT")
- `signal_type`: str, тип сигнала ("BUY", "SELL", "HOLD")
- `confidence_score`: float, оценка уверенности от 0 до 1
- `price_at_signal`: float, цена актива на момент сигнала
- `target_price`: Optional[float], целевая цена (опционально)
- `stop_loss`: Optional[float], уровень стоп-лосс (опционально)
- `time_frame`: str, временной фрейм анализа
- `expires_at`: Optional[datetime], время истечения сигнала (опционально)
- `technical_indicators`: Dict[str, float], значения технических индикаторов
- `smart_money_influence`: Optional[float], оценка влияния крупных игроков от -1 до 1 (опционально)
- `volatility_estimate`: Optional[float], оценка волатильности (опционально)

**Валидаторы:**
- Для `confidence_score`: значение должно быть от 0 до 1
- Для `smart_money_influence`: значение должно быть от -1 до 1
- Для `signal_type`: значение должно быть одним из ["BUY", "SELL", "HOLD"]
- Для `time_frame`: значение должно быть одним из ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]

#### SignalCreate

Модель для создания нового сигнала, наследуется от SignalBase.

**Дополнительные поля:**
- `xai_explanation`: Optional[XAIExplanationBase], данные для создания объяснения XAI (опционально)
- `related_news`: Optional[List[NewsRelevance]], связанные новости с оценкой релевантности (опционально)

#### SignalRead

Модель для базового чтения сигнала, наследуется от SignalBase.

**Дополнительные поля:**
- `id`: int, ID сигнала
- `created_at`: datetime, время создания сигнала
- `status`: str, статус сигнала ("ACTIVE", "EXPIRED", "TRIGGERED", "CANCELLED")
- `xai_explanation_id`: Optional[int], ID связанного XAI объяснения (опционально)

**Конфигурация:**
- `orm_mode = True` для совместимости с SQLAlchemy ORM

#### SignalDetailsRead

Расширенная модель для детального чтения сигнала, наследуется от SignalRead.

**Дополнительные поля:**
- `xai_explanation`: Optional[XAIExplanationBase], данные объяснения XAI (опционально)
- `related_news`: List[NewsRelevance], связанные новости с оценкой релевантности
- `trades_count`: int, количество сделок, связанных с сигналом
- `success_rate`: Optional[float], процент успешных сделок по этому сигналу (опционально)

**Конфигурация:**
- `orm_mode = True` для совместимости с SQLAlchemy ORM

#### SignalUpdate

Модель для обновления существующего сигнала.

**Поля:**
- `status`: Optional[str], новый статус сигнала (опционально)
- `target_price`: Optional[float], обновленная целевая цена (опционально)
- `stop_loss`: Optional[float], обновленный уровень стоп-лосс (опционально)
- `expires_at`: Optional[datetime], обновленное время истечения (опционально)

**Валидаторы:**
- Для `status`: значение должно быть одним из ["ACTIVE", "EXPIRED", "TRIGGERED", "CANCELLED"]

### Модели для списков сигналов

#### SignalList

Модель для возврата списка сигналов с пагинацией.

**Поля:**
- `items`: List[SignalRead], список сигналов
- `total`: int, общее количество сигналов
- `page`: int, текущая страница
- `size`: int, размер страницы
- `pages`: int, общее количество страниц

## Пример структуры файла

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime

# Вспомогательные модели для вложенных структур
class XAIExplanationBase(BaseModel):
    explanation_text: str
    factors_used: Dict[str, float]
    model_version: Optional[str] = None

class NewsBase(BaseModel):
    title: str
    source: str
    published_at: datetime
    sentiment_score: float
    url: Optional[str] = None
    
    @validator('sentiment_score')
    def validate_sentiment_score(cls, v):
        if not -1 <= v <= 1:
            raise ValueError('Sentiment score must be between -1 and 1')
        return v

class NewsRelevance(BaseModel):
    news: NewsBase
    relevance_score: float = Field(..., ge=0, le=1)
    impact_type: str
    
    @validator('impact_type')
    def validate_impact_type(cls, v):
        allowed_types = ["POSITIVE", "NEGATIVE", "NEUTRAL"]
        if v not in allowed_types:
            raise ValueError(f'Impact type must be one of {allowed_types}')
        return v

# Основные модели для сигналов
class SignalBase(BaseModel):
    asset_pair: str
    signal_type: str
    confidence_score: float = Field(..., ge=0, le=1)
    price_at_signal: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    time_frame: str
    expires_at: Optional[datetime] = None
    technical_indicators: Dict[str, float]
    smart_money_influence: Optional[float] = None
    volatility_estimate: Optional[float] = None
    
    @validator('signal_type')
    def validate_signal_type(cls, v):
        allowed_types = ["BUY", "SELL", "HOLD"]
        if v not in allowed_types:
            raise ValueError(f'Signal type must be one of {allowed_types}')
        return v
    
    @validator('time_frame')
    def validate_time_frame(cls, v):
        allowed_frames = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        if v not in allowed_frames:
            raise ValueError(f'Time frame must be one of {allowed_frames}')
        return v
    
    @validator('smart_money_influence')
    def validate_smart_money_influence(cls, v):
        if v is not None and not -1 <= v <= 1:
            raise ValueError('Smart money influence must be between -1 and 1')
        return v

# Остальные модели...
```

Пожалуйста, реализуй все модели согласно описанию выше, с правильными валидаторами и конфигурацией для совместимости с ORM.
