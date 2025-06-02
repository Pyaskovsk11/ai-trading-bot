# Техническое Задание: Интеграция Парсинга Новостей, AI и Базы Данных для Трейдинг-Бота

**Дата:** 21 мая 2025 г.

## 1. Введение

Настоящее техническое задание (ТЗ) описывает требования к разработке и интеграции системы парсинга новостей из различных источников (Twitter, Telegram-каналы, Arkham, Lookonchain), их обработке, сохранению в базу данных, анализу с помощью AI (включая Hector RAG) и использованию этой информации для улучшения торговых сигналов AI трейдинг-бота. ТЗ также включает механизмы фильтрации нерелевантного контента ("мусора") и очистки базы данных.

Документ учитывает предыдущие этапы разработки и результаты ревью проекта.

## 2. Цели проекта

- Обеспечить сбор актуальных новостей и данных из указанных источников в режиме, близком к реальному времени.
- Интегрировать полученные данные в существующую PostgreSQL базу данных.
- Использовать AI-модули (включая Hector RAG) для анализа текстовых данных, извлечения сущностей, определения тональности и генерации объяснений.
- Улучшить качество торговых сигналов за счет учета новостного фона и анализа действий крупных игроков.
- Реализовать эффективные механизмы фильтрации нерелевантной информации и очистки базы данных.
- Обеспечить соответствие кода стандартам качества (типизация, документация, тесты).

## 3. Архитектура Системы

Система будет состоять из следующих ключевых компонентов:

1.  **Модули Парсинга (Data Ingestion Layer)**:
    - **Twitter Parser**: Использует существующий Datasource API `Twitter/search_twitter` для получения твитов по ключевым словам, хэштегам и отслеживаемым аккаунтам.
    - **Telegram Parser**: Сервис для подключения к Telegram API (например, через библиотеку Telethon или Pyrogram) для мониторинга указанных каналов.
    - **Web Scrapers (Arkham, Lookonchain, новостные сайты)**: Набор скрейперов (например, на основе Scrapy или Playwright/Selenium для динамических сайтов) для извлечения данных с Arkham Intel, Lookonchain и других новостных порталов.
2.  **Модуль Предварительной Обработки и Фильтрации (Preprocessing & Filtering Layer)**:
    - Удаление дубликатов.
    - Фильтрация по ключевым словам, источникам, языку.
    - Очистка текста (удаление HTML-тегов, специальных символов).
    - Классификация "мусора" (спам, нерелевантные темы) с использованием AI-моделей (например, простой классификатор на основе TF-IDF и Logistic Regression или более сложная нейросеть).
3.  **Модуль Интеграции с Базой Данных (Data Storage Layer)**:
    - Сохранение очищенных и структурированных новостей в PostgreSQL.
    - Обновление существующих моделей данных и создание новых при необходимости (см. раздел 4).
4.  **Модуль AI-Анализа (AI Analysis Layer)**:
    - **Hector RAG**: Для анализа новостей, генерации объяснений и поиска релевантной информации по запросу.
    - **Sentiment Analysis**: Определение тональности новостей.
    - **Named Entity Recognition (NER)**: Извлечение ключевых сущностей (компании, персоны, криптовалюты).
    - **Event Detection**: Обнаружение значимых событий (например, крупные транзакции, партнерства).
    - **AI Prediction Model**: Модель, оценивающая потенциальное влияние новости на рынок или конкретный актив, и корректирующая уверенность торговых сигналов.
5.  **Модуль Интеграции с Торговой Логикой (Trading Logic Integration Layer)**:
    - Использование результатов AI-анализа для корректировки параметров торговых сигналов (например, изменение уровня уверенности, фильтрация сигналов).
6.  **Модуль Очистки Базы Данных (DB Maintenance Layer)**:
    - Периодическая архивация или удаление устаревших и нерелевантных данных.

## 4. База Данных

Необходимо расширить существующую схему БД PostgreSQL. Предлагаются следующие изменения и дополнения к файлу `app/db/models.py`:

```python
# ... (существующие импорты и модели)
import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLAlchemyEnum, Text, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base() # Если еще не определен или импортировать из существующего места

# --- Существующие модели (убедиться в наличии всех полей и связей) ---
class User(Base):
    __tablename__ = "users"
    # ... (поля как в предыдущем ТЗ по моделям)

class Signal(Base):
    __tablename__ = "signals"
    # ... (поля как в предыдущем ТЗ по моделям)
    # Добавить поле для влияния AI
    ai_confidence_modifier = Column(Float, nullable=True, comment="Модификатор уверенности от AI анализа новостей")
    related_news_ids = Column(JSON, nullable=True, comment="Список ID связанных новостей") # Или использовать связующую таблицу

class XAIExplanation(Base):
    __tablename__ = "xai_explanations"
    # ... (поля как в предыдущем ТЗ по моделям)

class Trade(Base):
    __tablename__ = "trades"
    # ... (поля как в предыдущем ТЗ по моделям)

# --- Новые модели для новостей и RAG ---
class NewsSourceType(enum.Enum):
    TWITTER = "twitter"
    TELEGRAM = "telegram"
    ARKHAM = "arkham"
    LOOKONCHAIN = "lookonchain"
    WEB = "web_generic"

class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(SQLAlchemyEnum(NewsSourceType), nullable=False, index=True)
    source_identifier = Column(String, nullable=False, comment="URL, ID твита, ID сообщения Telegram, etc.") # Уникальный идентификатор в источнике
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    raw_data = Column(JSON, nullable=True, comment="Полные сырые данные из источника")
    publication_date = Column(DateTime, nullable=False, index=True)
    parsed_date = Column(DateTime, default=datetime.utcnow)
    url = Column(String, nullable=True, unique=True)
    author = Column(String, nullable=True)
    language = Column(String(10), nullable=True)
    tags = Column(JSON, nullable=True, comment="Ключевые слова, хэштеги")

    # AI-related fields
    sentiment_score = Column(Float, nullable=True, comment="Оценка тональности от -1 до 1")
    sentiment_label = Column(String, nullable=True, comment="Позитивная, негативная, нейтральная")
    extracted_entities = Column(JSON, nullable=True, comment="Извлеченные сущности (криптовалюты, компании, персоны)")
    relevance_score = Column(Float, nullable=True, index=True, comment="Оценка релевантности новости к торговым активам/темам")
    is_spam = Column(Boolean, default=False, index=True, comment="Флаг спама/мусора")

    # Связь с сигналами (многие ко многим)
    # signals = relationship("Signal", secondary="signal_news_relevance", back_populates="news_articles") # Если нужна явная связь

    __table_args__ = (Index('ix_news_articles_source_identifier_source_type', 'source_identifier', 'source_type', unique=True),)

class RAGChunk(Base):
    __tablename__ = "rag_chunks"
    id = Column(Integer, primary_key=True, index=True)
    news_article_id = Column(Integer, ForeignKey('news_articles.id', ondelete="CASCADE"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_order = Column(Integer, nullable=False)
    # embedding_vector = Column(JSON, nullable=True) # Или использовать отдельную таблицу для векторов, если их много

    news_article = relationship("NewsArticle")

class RAGEmbedding(Base):
    __tablename__ = "rag_embeddings"
    id = Column(Integer, primary_key=True, index=True)
    rag_chunk_id = Column(Integer, ForeignKey('rag_chunks.id', ondelete="CASCADE"), nullable=False, unique=True)
    embedding_model_name = Column(String, nullable=False, default="all-MiniLM-L6-v2")
    vector = Column(JSON, nullable=False) # Хранение вектора как списка float

    rag_chunk = relationship("RAGChunk")

# Связующая таблица для Signal и NewsArticle (если нужна связь многие-ко-многим)
# class SignalNewsRelevance(Base):
#     __tablename__ = "signal_news_relevance"
#     signal_id = Column(Integer, ForeignKey('signals.id', ondelete="CASCADE"), primary_key=True)
#     news_article_id = Column(Integer, ForeignKey('news_articles.id', ondelete="CASCADE"), primary_key=True)
#     relevance_score_to_signal = Column(Float, nullable=True)
#     explanation = Column(Text, nullable=True)

# --- Добавить индексы для существующих моделей, если не были добавлены ранее ---
# Пример для Signal:
# Index('ix_signals_asset_pair_status_created_at', Signal.asset_pair, Signal.status, Signal.created_at.desc()),

# ... (остальные модели и их обновление/дополнение)
```

**Миграции**: Использовать Alembic для создания и применения миграций базы данных.

## 5. Реализация Компонентов

### 5.1. Модули Парсинга

Создать сервисы в `app/services/` для каждого источника:

- **`twitter_service.py`**:
  - Использовать `ApiClient` для вызова `Twitter/search_twitter`.
  - Реализовать логику пагинации с использованием `cursor`.
  - Преобразовывать ответ API в стандартизированный формат `NewsArticle`.
  - Обрабатывать ошибки API, управлять лимитами запросов.
- **`telegram_service.py`**:
  - Использовать `Telethon` или `Pyrogram`.
  - Настройка для подключения к указанным каналам (требуется аутентификация).
  - Обработка новых сообщений, извлечение текста, метаданных.
  - Преобразование в формат `NewsArticle`.
- **`web_scraper_service.py`**:
  - Отдельные классы или функции для Arkham, Lookonchain и общих новостных сайтов.
  - Использовать `requests` + `BeautifulSoup` для статических сайтов, `Playwright` или `Selenium` для динамических.
  - Обработка robots.txt, управление User-Agent, задержки между запросами.
  - Извлечение заголовка, текста, даты публикации, автора, URL.
  - Преобразование в формат `NewsArticle`.

**Общие требования к парсерам**:

- Асинхронная работа (использовать `async/await` и `httpx` или `aiohttp`).
- Конфигурируемость (список ключевых слов, каналов, сайтов через `app/core/config.py`).
- Логирование операций и ошибок.
- Сохранение сырых данных в `NewsArticle.raw_data` для отладки и повторной обработки.

### 5.2. Модуль Предварительной Обработки и Фильтрации

Создать сервис `app/services/news_processing_service.py`:

- **`process_raw_article(raw_article_data, source_type)`**:
  - Принимает сырые данные от парсера.
  - **Дедупликация**: Проверка на наличие новости в БД по `source_identifier` и `source_type` или по схожести контента (например, через хэши или shingles).
  - **Очистка текста**: Удаление HTML, лишних пробелов, спецсимволов.
  - **Определение языка** (если не предоставлен источником).
  - **Фильтрация по ключевым словам/темам**: Отбрасывать новости, не содержащие релевантных терминов.
  - **Классификация "мусора"**:
    - Интеграция с простой AI-моделью (обученной отдельно или использование готовых решений) для определения спама/нерелевантных новостей.
    - Установка флага `NewsArticle.is_spam`.
    - Нерелевантные новости могут либо не сохраняться, либо сохраняться с флагом для последующего анализа/удаления.
  - Сохранение обработанной новости в БД через `NewsArticleRepository`.

### 5.3. Модуль Интеграции с Базой Данных

Создать репозитории в `app/db/repositories/` (например, `news_repository.py`):

- **`NewsArticleRepository`**: CRUD-операции для `NewsArticle`, поиск, фильтрация.
- **`RAGChunkRepository`**, **`RAGEmbeddingRepository`**: для управления чанками и их эмбеддингами.

### 5.4. Модуль AI-Анализа

Создать сервисы в `app/services/ai/`:

- **`sentiment_service.py`**:
  - Использование предобученной модели (например, из `transformers` library: `cardiffnlp/twitter-roberta-base-sentiment` или аналогичной для финансовых текстов) или внешнего API.
  - Обновление полей `NewsArticle.sentiment_score`, `NewsArticle.sentiment_label`.
- **`ner_service.py`**:
  - Использование `spaCy` или `transformers` для извлечения криптовалют, компаний, персон.
  - Обновление поля `NewsArticle.extracted_entities`.
- **`hector_rag_service.py` (или `rag_pipeline_service.py`)**:
  - **Чанкинг**: Разделение `NewsArticle.content` на более мелкие чанки (`RAGChunk`).
  - **Генерация эмбеддингов**: Для каждого чанка генерировать векторное представление с помощью модели типа Sentence Transformers (e.g., `all-MiniLM-L6-v2`). Сохранять в `RAGEmbedding`.
  - **Поиск по сходству**: Реализовать функцию поиска наиболее релевантных чанков по векторному запросу (использовать FAISS, Annoy или простой косинусный поиск для начала).
  - **Генерация ответа (опционально для RAG)**: Если RAG используется для ответов на вопросы, интегрировать с LLM для генерации ответа на основе найденных чанков.
- **`news_relevance_service.py`**:
  - Оценка релевантности новости к отслеживаемым активам или торговым темам (может быть основана на наличии ключевых слов, сущностей, или более сложная модель).
  - Обновление поля `NewsArticle.relevance_score`.
- **`signal_ai_modifier_service.py`**:
  - Анализирует последние релевантные новости (с высоким `relevance_score` и не `is_spam`) для актива, по которому сгенерирован сигнал.
  - Использует агрегированную тональность, наличие ключевых событий или предсказание отдельной AI-модели для корректировки уверенности сигнала (`Signal.ai_confidence_modifier`).

### 5.5. Модуль Очистки Базы Данных

Создать сервис `app/services/db_maintenance_service.py` или скрипт для периодического запуска (например, через Celery beat или системный cron):

- **`cleanup_old_news()`**:
  - Удаление или архивация новостей старше определенного срока (например, 3-6 месяцев), если они не связаны с активными сделками или важными историческими сигналами.
  - Удаление новостей с низким `relevance_score` или помеченных как `is_spam` после определенного периода.
- **`cleanup_orphan_data()`**: Удаление связанных данных (чанки, эмбеддинги) при удалении `NewsArticle` (обеспечивается через `ondelete="CASCADE"` в моделях, но можно добавить явную проверку).

## 6. Пайплайн Обработки Новостей

1.  Парсеры собирают данные из источников.
2.  Сырые данные передаются в `NewsProcessingService`.
3.  Происходит дедупликация, очистка, фильтрация, классификация на спам.
4.  Если новость не спам и релевантна, она сохраняется в `NewsArticle`.
5.  Асинхронные задачи (например, через Celery или FastAPI BackgroundTasks) запускаются для AI-анализа сохраненной новости:
    - Расчет тональности.
    - Извлечение сущностей.
    - Оценка релевантности.
    - Чанкинг и генерация эмбеддингов для RAG.
6.  При генерации нового торгового сигнала, `SignalAIMoifierService` запрашивает релевантные новости и их AI-анализ для корректировки сигнала.

## 7. Учет Замечаний из Ревью Проекта

- **Типизация**: Весь новый Python код должен использовать type hints.
- **Docstrings**: Все функции, классы и методы должны иметь подробные docstrings (например, в стиле Google или NumPy).
- **README.md**: Обновить README.md инструкциями по настройке и запуску новых сервисов парсинга и AI-анализа.
- **Тесты**:
  - Unit-тесты для каждого сервиса и функции (особенно для логики обработки, фильтрации, AI-анализа).
  - Интеграционные тесты для проверки взаимодействия парсеров с `NewsProcessingService` и БД.
  - Мокировать внешние API (Twitter, Telegram, веб-сайты) при тестировании парсеров.
- **Индексы БД**: Добавить необходимые индексы в модели `NewsArticle`, `RAGChunk`, `RAGEmbedding` и другие для оптимизации запросов (примеры приведены в разделе 4).
- **Валидация данных на уровне БД**: Использовать `CheckConstraint` в SQLAlchemy моделях, где это применимо.
- **Документация API**: Если для новых сервисов создаются API эндпоинты, обновить документацию Swagger/OpenAPI.
- **Безопасность**:
  - Безопасное хранение API-ключей для Telegram и других сервисов (использовать переменные окружения и `app/core/config.py`).
  - Учитывать этические аспекты при парсинге и использовании данных.
- **Производительность**:
  - Использовать асинхронные операции для I/O bound задач (парсинг, AI-выводы через API).
  - Оптимизировать запросы к БД.
  - Рассмотреть использование кэширования для часто запрашиваемых AI-результатов или новостей.
- **Логирование**: Детальное логирование всех этапов парсинга, обработки и анализа новостей.

## 8. План Реализации (Предложение)

1.  **Этап 1: Базовая инфраструктура новостей**
    - Реализация моделей `NewsArticle`, `RAGChunk`, `RAGEmbedding` и миграций.
    - Реализация `NewsArticleRepository`.
    - Реализация парсера для одного источника (например, Twitter через Datasource API).
    - Базовая предварительная обработка (очистка, дедупликация).
2.  **Этап 2: Расширение парсинга и фильтрация**
    - Реализация парсеров для Telegram, Arkham, Lookonchain.
    - Реализация классификатора спама/мусора (начальная версия).
    - Настройка пайплайна сохранения новостей в БД.
3.  **Этап 3: Интеграция AI-анализа**
    - Интеграция сервисов для Sentiment Analysis, NER, News Relevance.
    - Реализация чанкинга и генерации эмбеддингов для RAG.
4.  **Этап 4: Влияние AI на сигналы и RAG**
    - Реализация `SignalAIMoifierService`.
    - Интеграция RAG для поиска по новостям (если требуется функционал вопросов-ответов или поиска похожих новостей).
5.  **Этап 5: Очистка БД и оптимизация**
    - Реализация `DBMaintenanceService`.
    - Профилирование и оптимизация производительности.
6.  **Этап 6: Тестирование и Документация**
    - Написание полного комплекта тестов.
    - Обновление всей документации.

## 9. Требования к Окружению и Зависимостям

- Python 3.9+
- PostgreSQL 12+
- FastAPI, SQLAlchemy, Alembic, Pydantic
- Библиотеки для парсинга: `httpx`, `beautifulsoup4`, `playwright` (или `selenium`), `telethon` (или `pyrogram`), `scrapy` (опционально).
- Библиотеки для AI: `transformers`, `sentence-transformers`, `spacy`, `scikit-learn`, `faiss-cpu` (или `annoy`).
- Celery (или другой менеджер задач) для фоновой обработки.

## 10. Ожидаемые Результаты

- Рабочая система сбора, обработки и анализа новостей из указанных источников.
- Интеграция новостных данных и результатов AI-анализа в процесс генерации торговых сигналов.
- Механизмы для поддержания качества и актуальности данных в новостной базе.
- Код, соответствующий стандартам качества, с документацией и тестами.

Этот промпт/ТЗ должен быть использован как основа для AI-агента Cursor для генерации кода и структуры проекта. Каждый раздел можно детализировать дополнительными промптами по мере необходимости.
