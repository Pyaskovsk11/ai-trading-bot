# 🗄️ Руководство по миграции базы данных

## Миграция с SQLite на PostgreSQL + Redis

Это руководство поможет вам мигрировать AI Trading Bot с SQLite на производственную конфигурацию с PostgreSQL и Redis.

---

## 📋 Что изменилось

### ✅ **Было (SQLite)**
- Локальная файловая база данных
- Ограниченная масштабируемость
- Нет кэширования
- Проблемы с параллелизмом

### 🚀 **Стало (PostgreSQL + Redis)**
- Промышленная СУБД PostgreSQL
- Полная поддержка ACID транзакций
- Масштабируемость и репликация
- Redis для кэширования и сессий
- Партиционирование таблиц
- Оптимизированные индексы

---

## 🛠️ Установка и настройка

### 1. **Запуск PostgreSQL и Redis через Docker**

```bash
# Запуск всех сервисов
docker-compose up -d postgres redis

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs postgres
docker-compose logs redis
```

### 2. **Установка зависимостей**

```bash
# Установка новых зависимостей
pip install -r requirements.txt

# Основные новые пакеты:
# - psycopg2-binary (PostgreSQL драйвер)
# - asyncpg (асинхронный PostgreSQL)
# - redis, aioredis (Redis клиенты)
# - SQLAlchemy 2.0+ (современный ORM)
```

### 3. **Настройка переменных окружения**

```bash
# Скопируйте пример конфигурации
cp database.env.example .env

# Отредактируйте .env файл с вашими настройками
nano .env
```

**Основные переменные:**
```env
# PostgreSQL
DB_POSTGRES_HOST=localhost
DB_POSTGRES_PORT=5432
DB_POSTGRES_USER=trading_user
DB_POSTGRES_PASSWORD=trading_password_2025
DB_POSTGRES_DB=trading_bot

# Redis
DB_REDIS_HOST=localhost
DB_REDIS_PORT=6379
DB_REDIS_PASSWORD=redis_password_2025
```

---

## 🗃️ Структура новой базы данных

### **Схемы:**
- `trading` - основные торговые данные
- `analytics` - аналитика и метрики
- `logs` - логирование приложения

### **Основные таблицы:**

#### Trading Schema
- `users` - пользователи и аутентификация
- `trading_pairs` - торговые пары
- `market_data` - рыночные данные (партиционированная)
- `trading_orders` - торговые ордера
- `trading_signals` - AI сигналы
- `portfolios` - портфели пользователей
- `portfolio_positions` - позиции в портфелях
- `ml_model_performance` - метрики ML моделей

#### Analytics Schema
- `daily_portfolio_snapshots` - ежедневные снимки портфелей
- `trading_performance` - торговая статистика

#### Logs Schema
- `app_logs` - логи приложения
- `api_logs` - логи API запросов

---

## 🧪 Тестирование миграции

### **Автоматическое тестирование:**

```bash
# Запуск полного теста миграции
python test_database_migration.py
```

**Тесты включают:**
- ✅ Подключение к PostgreSQL
- ✅ Подключение к Redis
- ✅ Тестирование CacheManager
- ✅ Проверка ORM моделей
- ✅ CRUD операции
- ✅ Тестирование производительности

### **Ручная проверка:**

```bash
# Подключение к PostgreSQL
docker exec -it trading_bot_postgres psql -U trading_user -d trading_bot

# Проверка таблиц
\dt trading.*
\dt analytics.*
\dt logs.*

# Проверка данных
SELECT COUNT(*) FROM trading.trading_pairs;
SELECT COUNT(*) FROM trading.users;
```

```bash
# Подключение к Redis
docker exec -it trading_bot_redis redis-cli -a redis_password_2025

# Проверка Redis
PING
INFO memory
DBSIZE
```

---

## 🔄 Миграция данных (если нужно)

### **Если у вас есть данные в SQLite:**

1. **Экспорт данных из SQLite:**
```python
# Создайте скрипт export_sqlite_data.py
import sqlite3
import json

def export_sqlite_data():
    conn = sqlite3.connect('trading_bot.db')
    cursor = conn.cursor()
    
    # Экспорт пользователей
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    with open('users_export.json', 'w') as f:
        json.dump(users, f)
    
    # Аналогично для других таблиц
    conn.close()
```

2. **Импорт в PostgreSQL:**
```python
# Создайте скрипт import_to_postgresql.py
import asyncio
import json
from app.config.database import db_manager
from app.models.user import User

async def import_users():
    with open('users_export.json', 'r') as f:
        users_data = json.load(f)
    
    async with db_manager.get_postgres_session() as session:
        for user_data in users_data:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                # ... другие поля
            )
            session.add(user)
        await session.commit()
```

---

## 🚀 Запуск с новой БД

### **1. Обновление кода приложения:**

```python
# В main.py или app.py
from app.config.database import db_manager

@app.on_event("startup")
async def startup_event():
    await db_manager.initialize()
    print("✅ Database connections initialized")

@app.on_event("shutdown")
async def shutdown_event():
    await db_manager.close()
    print("🔌 Database connections closed")
```

### **2. Использование в API endpoints:**

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db_session, get_cache_manager

@app.get("/users")
async def get_users(
    db: AsyncSession = Depends(get_db_session),
    cache: CacheManager = Depends(get_cache_manager)
):
    # Проверяем кэш
    cached_users = await cache.get("users:all")
    if cached_users:
        return json.loads(cached_users)
    
    # Запрос к БД
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    # Сохраняем в кэш
    await cache.set("users:all", json.dumps([u.to_dict() for u in users]), expire=300)
    
    return users
```

---

## 📊 Мониторинг и обслуживание

### **Health Check API:**
```bash
# Проверка состояния БД
curl http://localhost:8000/api/database/health

# Информация о PostgreSQL
curl http://localhost:8000/api/database/info

# Информация о Redis
curl http://localhost:8000/api/database/redis/info
```

### **pgAdmin (веб-интерфейс для PostgreSQL):**
- URL: http://localhost:8080
- Email: admin@tradingbot.local
- Password: admin_password_2025

### **Резервное копирование:**

```bash
# Backup PostgreSQL
docker exec trading_bot_postgres pg_dump -U trading_user trading_bot > backup_$(date +%Y%m%d).sql

# Restore PostgreSQL
docker exec -i trading_bot_postgres psql -U trading_user trading_bot < backup_20250125.sql

# Backup Redis
docker exec trading_bot_redis redis-cli -a redis_password_2025 --rdb /data/backup.rdb
```

---

## ⚡ Оптимизация производительности

### **PostgreSQL настройки:**
```sql
-- Анализ производительности
EXPLAIN ANALYZE SELECT * FROM trading.market_data WHERE symbol = 'BTC-USDT';

-- Обновление статистики
ANALYZE;

-- Проверка размеров таблиц
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname IN ('trading', 'analytics', 'logs')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### **Redis оптимизация:**
```bash
# Мониторинг Redis
redis-cli -a redis_password_2025 INFO memory
redis-cli -a redis_password_2025 INFO stats

# Очистка истекших ключей
redis-cli -a redis_password_2025 --scan --pattern "expired:*" | xargs redis-cli -a redis_password_2025 DEL
```

---

## 🔧 Устранение неполадок

### **Частые проблемы:**

1. **Ошибка подключения к PostgreSQL:**
```bash
# Проверка статуса контейнера
docker-compose ps postgres

# Проверка логов
docker-compose logs postgres

# Перезапуск
docker-compose restart postgres
```

2. **Ошибка подключения к Redis:**
```bash
# Проверка Redis
docker exec trading_bot_redis redis-cli -a redis_password_2025 ping

# Проверка конфигурации
docker exec trading_bot_redis cat /usr/local/etc/redis/redis.conf
```

3. **Проблемы с миграцией схемы:**
```sql
-- Проверка существования схем
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name IN ('trading', 'analytics', 'logs');

-- Пересоздание схемы (ОСТОРОЖНО!)
DROP SCHEMA IF EXISTS trading CASCADE;
-- Затем запустите инициализацию заново
```

---

## 📈 Преимущества новой архитектуры

### **PostgreSQL:**
- ✅ ACID транзакции
- ✅ Параллельные запросы
- ✅ Партиционирование таблиц
- ✅ Репликация и масштабирование
- ✅ Богатые типы данных (JSON, UUID, INET)
- ✅ Полнотекстовый поиск

### **Redis:**
- ✅ Кэширование API ответов
- ✅ Хранение сессий пользователей
- ✅ Rate limiting
- ✅ Pub/Sub для real-time уведомлений
- ✅ Высокая производительность (микросекунды)

### **Общие улучшения:**
- ✅ Готовность к продакшену
- ✅ Горизонтальное масштабирование
- ✅ Улучшенная производительность
- ✅ Профессиональный мониторинг
- ✅ Автоматическое резервное копирование

---

## 🎯 Следующие шаги

После успешной миграции рекомендуется:

1. **Настроить мониторинг** (Prometheus + Grafana)
2. **Внедрить аутентификацию** (JWT токены)
3. **Добавить rate limiting**
4. **Настроить CI/CD pipeline**
5. **Создать backup стратегию**

---

**🎉 Поздравляем! Ваш AI Trading Bot теперь работает на промышленной архитектуре БД!** 