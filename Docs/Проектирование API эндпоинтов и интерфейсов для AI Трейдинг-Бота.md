## Проектирование API эндпоинтов и интерфейсов для AI Трейдинг-Бота

Этот документ описывает REST API эндпоинты для backend-части на FastAPI, а также структуру взаимодействия с Telegram-ботом и веб-интерфейсом на React. Проектирование выполнено с учетом "Cursor Project Rules" и требований к изоляции логики.

### 1. FastAPI API Эндпоинты (`app/api/`)

Все эндпоинты будут использовать префикс `/api/v1/`. Для ответов и запросов будут использоваться Pydantic модели для валидации и сериализации данных.

#### 1.1. Сигналы (`app/api/signals.py`)

*   **`GET /signals/`**: Получение списка торговых сигналов.
    *   **Параметры запроса (query params)**:
        *   `skip: int = 0`: Количество пропускаемых записей (для пагинации).
        *   `limit: int = 100`: Максимальное количество записей (для пагинации).
        *   `coin_pair: Optional[str] = None`: Фильтр по торговой паре (например, `BTC/USDT`).
        *   `signal_type: Optional[str] = None`: Фильтр по типу сигнала (`LONG`, `SHORT`).
        *   `date_from: Optional[datetime] = None`: Фильтр по дате начала.
        *   `date_to: Optional[datetime] = None`: Фильтр по дате окончания.
        *   `result: Optional[str] = None`: Фильтр по результату сигнала (`TP_HIT`, `SL_HIT`).
    *   **Ответ**: Список объектов сигналов (включая основные данные и ID XAI-объяснения).
    *   **Пример Pydantic модели ответа (SignalRead)**: `id`, `coin_pair`, `timestamp`, `signal_type`, `entry_price_target`, `take_profit_target`, `stop_loss_target`, `indicators_data` (JSON), `news_sentiment_score`, `smart_money_activity` (JSON), `xai_explanation_id`, `result`.

*   **`GET /signals/{signal_id}/`**: Получение детальной информации о конкретном сигнале.
    *   **Параметры пути (path params)**: `signal_id: int`.
    *   **Ответ**: Объект сигнала, включающий полный текст XAI-объяснения (через join с таблицей `xai_explanations` или отдельный запрос).
    *   **Пример Pydantic модели ответа (SignalDetailsRead)**: `SignalRead` + `xai_explanation_text`.

#### 1.2. Сделки (Симулированные) (`app/api/trades.py`)

*   **`GET /trades/`**: Получение списка симулированных сделок.
    *   **Параметры запроса (query params)**: `skip`, `limit`, `coin_pair`, `status`, `date_from`, `date_to`.
    *   **Ответ**: Список объектов сделок.
    *   **Пример Pydantic модели ответа (TradeRead)**: `id`, `signal_id`, `entry_price`, `exit_price`, `quantity`, `pnl`, `pnl_percentage`, `status`, `opened_at`, `closed_at`.

*   **`GET /trades/{trade_id}/`**: Получение информации о конкретной сделке.
    *   **Параметры пути (path params)**: `trade_id: int`.
    *   **Ответ**: Объект сделки.

#### 1.3. Новости (`app/api/news.py`)

*   **`GET /news/`**: Получение списка обработанных новостей.
    *   **Параметры запроса (query params)**: `skip`, `limit`, `affected_asset: Optional[str] = None`, `date_from`, `date_to`, `min_sentiment_score: Optional[float] = None`.
    *   **Ответ**: Список объектов новостей.
    *   **Пример Pydantic модели ответа (NewsRead)**: `id`, `source_url`, `title`, `published_at`, `content_summary`, `affected_assets` (JSON), `sentiment_score`, `relevance_score`.

#### 1.4. Статистика и Сводки (`app/api/summary.py`)

*   **`GET /summary/general/`**: Получение общей статистики по эффективности сигналов/сделок.
    *   **Ответ**: JSON объект со статистикой (например, общий PnL, % прибыльных сделок, средний PnL на сделку, количество сигналов по типам).
    *   **Пример Pydantic модели ответа (GeneralSummary)**: `total_simulated_trades`, `win_rate`, `total_pnl`, `average_pnl_per_trade`, `signals_by_type`.

*   **`GET /summary/asset/{coin_pair}/`**: Получение статистики по конкретной торговой паре.
    *   **Параметры пути (path params)**: `coin_pair: str`.
    *   **Ответ**: JSON объект со статистикой для указанной пары.
    *   **Пример Pydantic модели ответа (AssetSummary)**: Аналогично `GeneralSummary`, но для конкретного актива.

#### 1.5. Статус Бота (`app/api/status.py`)

*   **`GET /status/`**: Получение текущего операционного статуса бота.
    *   **Ответ**: JSON объект со статусом (например, `{"status": "operational", "last_data_fetch_prices": "timestamp", "last_data_fetch_news": "timestamp", "active_assets_tracking": ["BTC/USDT", "ETH/USDT"]}`).
    *   **Пример Pydantic модели ответа (BotStatus)**: `status`, `last_data_fetch_prices`, `last_data_fetch_news`, `active_assets_tracking`.

#### 1.6. Управление Пользователями (Whitelist - для администратора) (`app/api/users.py`)

Эти эндпоинты потребуют аутентификации и авторизации администратора.

*   **`POST /users/`**: Добавление пользователя в белый список.
    *   **Тело запроса (UserCreate)**: `telegram_id: Optional[int]`, `username: Optional[str]`, `email: Optional[str]`.
    *   **Ответ**: Объект созданного пользователя.
*   **`GET /users/`**: Получение списка пользователей из белого списка.
    *   **Ответ**: Список объектов пользователей.
*   **`PUT /users/{user_id}/whitelist_status/`**: Изменение статуса `is_whitelisted` для пользователя.
    *   **Тело запроса (UserWhitelistUpdate)**: `is_whitelisted: bool`.
    *   **Ответ**: Обновленный объект пользователя.
*   **`DELETE /users/{user_id}/`**: Удаление пользователя.
    *   **Ответ**: Сообщение об успехе.

### 2. Интерфейс Telegram-бота (`telegram_bot/`)

Telegram-бот будет взаимодействовать с API FastAPI для получения данных. Пользователи не могут управлять сделками, только получать информацию.

*   **Команды**:
    *   `/start`: Приветственное сообщение, краткое описание бота и доступных команд. Упоминание, что информация предоставляется в ознакомительных целях и не гарантирует прибыль.
    *   `/status`: Запрашивает `GET /api/v1/status/` и отображает текущий статус работы бота.
    *   `/signal` (или `/latest_signal`): Запрашивает `GET /api/v1/signals/?limit=1&sort_by=-timestamp` (или несколько последних). Отображает ключевую информацию по последнему(им) сигналу(ам): пара, тип, цена входа, TP, SL и краткое XAI-объяснение.
    *   `/summary`: Запрашивает `GET /api/v1/summary/general/` и отображает общую сводку по эффективности (симулированных) сделок.
*   **Уведомления о новых сигналах**: При генерации нового сигнала и его сохранении в БД, backend может (через механизм очередей или прямой вызов, если архитектура позволяет) инициировать отправку уведомления через Telegram-бота всем пользователям из белого списка. Уведомление должно содержать ту же информацию, что и команда `/signal`.
*   **Соблюдение User Rules**: Бот должен явно информировать пользователей об ограничениях и рисках.

### 3. Веб-интерфейс (`webapp/` - React)

Веб-интерфейс предоставляет только чтение и визуализацию данных, получаемых через API FastAPI.

*   **Аутентификация (Опционально)**: Если доступ к веб-интерфейсу должен быть ограничен, можно реализовать систему входа для пользователей из белого списка (например, по email/паролю или через Telegram OAuth).
*   **Основные разделы**:
    *   **Панель сигналов (Dashboard)**:
        *   Отображение списка сигналов (получение данных с `GET /api/v1/signals/`).
        *   **Фильтрация**: По торговой паре, дате, типу сигнала, результату.
        *   **Сортировка**: По дате, по паре и т.д.
        *   **Детальный просмотр сигнала**: При клике на сигнал открывается страница/модальное окно с полной информацией (данные с `GET /api/v1/signals/{signal_id}/`), включая полное XAI-объяснение.
        *   **Визуализация**: Для каждого сигнала (или на отдельной странице актива) могут отображаться графики цен (например, с использованием TradingView Lightweight Charts или другой библиотеки) с нанесенными метками входа, TP, SL.
    *   **Статистика и Аналитика**:
        *   Отображение общей статистики (данные с `GET /api/v1/summary/general/`) и статистики по отдельным активам (данные с `GET /api/v1/summary/asset/{coin_pair}/`).
        *   Представление данных в виде таблиц и графиков (например, кривая доходности симулированных сделок, распределение PnL).
    *   **Лента новостей**:
        *   Отображение списка проанализированных новостей (данные с `GET /api/v1/news/`).
        *   Фильтрация по затронутым активам, дате, источнику.
        *   Возможность просмотра краткого содержания и оценки влияния.
    *   **Информация для пользователя**: Четкое отображение дисклеймеров о рисках, об ознакомительном характере информации, и что бот не гарантирует прибыль.

### 4. Pydantic Модели (Примеры)

В `app/schemas.py` (или аналогичном файле) будут определены Pydantic модели для валидации данных в API.

```python
# Пример для app/schemas/signal.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class SignalBase(BaseModel):
    coin_pair: str
    signal_type: str
    entry_price_target: Optional[float] = None
    take_profit_target: Optional[float] = None
    stop_loss_target: Optional[float] = None
    indicators_data: Dict[str, Any]
    news_sentiment_score: Optional[float] = None
    smart_money_activity: Optional[Dict[str, Any]] = None
    result: Optional[str] = None

class SignalRead(SignalBase):
    id: int
    timestamp: datetime
    xai_explanation_id: int

    class Config:
        orm_mode = True

class SignalDetailsRead(SignalRead):
    xai_explanation_text: str

# ... другие модели для Trades, News, Users, Summary, Status
```

Этот дизайн API и интерфейсов обеспечивает разделение логики, предоставляет необходимые данные для Telegram-бота и веб-приложения, а также учитывает правила и ограничения, указанные пользователем.
