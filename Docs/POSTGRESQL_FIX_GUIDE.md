# 🔧 Руководство по исправлению PostgreSQL проблем

## 🚨 **Обнаруженная проблема**

**Ошибка:** PostgreSQL 15 не может запуститься из-за конфликта с данными PostgreSQL 13

```
FATAL: database files are incompatible with server
DETAIL: The data directory was initialized by PostgreSQL version 13, 
which is not compatible with this version 15.13.
```

**Причина:** 
- Старый контейнер PostgreSQL 13 занимает порт 5432
- Новый контейнер PostgreSQL 15 пытается использовать данные от версии 13
- Docker volumes содержат несовместимые данные

---

## 🛠️ **Пошаговое решение**

### **Шаг 1: Остановить все контейнеры**
```bash
# Остановить все связанные контейнеры
docker-compose down

# Остановить старый PostgreSQL 13 контейнер
docker stop ai_trading_bot-db-1

# Удалить старый контейнер
docker rm ai_trading_bot-db-1
```

### **Шаг 2: Очистить Docker volumes**
```bash
# Посмотреть все volumes
docker volume ls

# Удалить volumes PostgreSQL (ОСТОРОЖНО - удалит данные!)
docker volume rm ai_trading_bot_postgres_data
docker volume rm trading_bot_postgres_data

# Или удалить все неиспользуемые volumes
docker volume prune -f
```

### **Шаг 3: Обновить docker-compose.yml**
```yaml
# Убедиться что порт правильный
services:
  postgres:
    image: postgres:15-alpine
    container_name: trading_bot_postgres
    ports:
      - "5432:5432"  # Изменить обратно на 5432
    volumes:
      - postgres_data_v15:/var/lib/postgresql/data  # Новое имя volume
```

### **Шаг 4: Обновить конфигурацию приложения**
```python
# В app/config/database.py
class DatabaseSettings(BaseSettings):
    postgres_port: int = 5432  # Изменить обратно на 5432
```

### **Шаг 5: Запустить заново**
```bash
# Запустить PostgreSQL и Redis
docker-compose up -d postgres redis

# Проверить статус
docker-compose ps

# Проверить логи
docker-compose logs postgres
```

---

## 🧪 **Тестирование исправления**

### **Проверка подключения:**
```bash
# Тест подключения к PostgreSQL
docker exec -it trading_bot_postgres psql -U trading_user -d trading_bot -c "SELECT version();"

# Тест подключения к Redis
docker exec -it trading_bot_redis redis-cli -a redis_password_2025 ping
```

### **Запуск тестов миграции:**
```bash
python test_database_migration.py
```

**Ожидаемый результат:**
```
✅ PostgreSQL Connection: ПРОЙДЕН
✅ Redis Connection: ПРОЙДЕН
✅ Cache Manager: ПРОЙДЕН
✅ Database Models: ПРОЙДЕН
✅ CRUD Operations: ПРОЙДЕН
✅ Performance: ПРОЙДЕН
```

---

## 🔄 **Альтернативное решение (если нужны данные)**

Если в старой БД есть важные данные, можно сделать миграцию:

### **Экспорт данных из PostgreSQL 13:**
```bash
# Создать дамп данных
docker exec ai_trading_bot-db-1 pg_dump -U postgres -d trading_bot > backup_pg13.sql

# Или экспорт только схемы
docker exec ai_trading_bot-db-1 pg_dump -U postgres -d trading_bot --schema-only > schema_pg13.sql
```

### **Импорт в PostgreSQL 15:**
```bash
# После запуска нового контейнера
docker exec -i trading_bot_postgres psql -U trading_user -d trading_bot < backup_pg13.sql
```

---

## 📋 **Команды для быстрого исправления**

```bash
# 1. Полная очистка
docker-compose down
docker stop ai_trading_bot-db-1
docker rm ai_trading_bot-db-1
docker volume prune -f

# 2. Обновить порт в .env
echo "DB_POSTGRES_PORT=5432" >> .env

# 3. Запустить заново
docker-compose up -d postgres redis

# 4. Проверить
docker-compose ps
docker-compose logs postgres

# 5. Тест
python test_database_migration.py
```

---

## ⚠️ **Важные замечания**

1. **Потеря данных:** Очистка volumes удалит все данные
2. **Порты:** Убедитесь что порт 5432 свободен
3. **Конфигурация:** Обновите все файлы конфигурации
4. **Тестирование:** Обязательно запустите тесты после исправления

---

## 🎯 **После исправления**

После успешного исправления PostgreSQL проблем можно переходить к:

1. **Унификации торговых стратегий**
2. **Реализации продвинутого риск-менеджмента**
3. **Интеграции всех компонентов**

**Проект готов стать профессиональной торговой системой!** 🚀 