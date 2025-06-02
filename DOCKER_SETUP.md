# 🐳 Docker Setup - AI Trading Bot

## Обзор проблемы
Проблема с scikit-learn часто возникает в Windows из-за конфликтов при компиляции C-библиотек. Docker решает эту проблему путем создания изолированной Linux-среды.

## ⚡ Быстрый запуск

### Windows (PowerShell):
```powershell
.\docker-start.ps1
```

### Linux/macOS (Bash):
```bash
chmod +x docker-start.sh
./docker-start.sh
```

## 📋 Требования

### 1. Docker Desktop
- **Windows**: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- **macOS**: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- **Linux**: [Docker Engine](https://docs.docker.com/engine/install/)

### 2. Минимальные системные требования
- RAM: 8GB (рекомендуется 16GB)
- Свободное место: 10GB
- CPU: 4 ядра (рекомендуется)

## 🏗️ Архитектура Docker

```mermaid
graph TB
    subgraph "Docker Network: trading_network"
        A[Frontend :3000] --> B[Backend :8000]
        B --> C[PostgreSQL :5432]
        B --> D[Redis :6379]
        E[Telegram Bot] --> B
        F[pgAdmin :8080] --> C
    end
```

## 🚀 Сервисы

| Сервис | Порт | Описание | Здоровье |
|--------|------|----------|----------|
| **Backend API** | 8000 | FastAPI приложение | `/health` |
| **Frontend** | 3000 | React интерфейс | Статический |
| **PostgreSQL** | 5432 | База данных | `pg_isready` |
| **Redis** | 6379 | Кэш и сессии | `redis-cli ping` |
| **Telegram Bot** | - | Telegram интеграция | Фоновый |
| **pgAdmin** | 8080 | Управление БД | Web UI |

## 🔧 Конфигурация

### Переменные окружения (docker-compose.yml)
```yaml
environment:
  - DATABASE_URL=postgresql://trading_user:trading_password_2025@postgres:5432/trading_bot
  - REDIS_URL=redis://:redis_password_2025@redis:6379/0
  - USE_DEMO_ACCOUNT=true
  - ENABLE_REAL_TRADING=false
```

### Доступы по умолчанию
- **PostgreSQL**: 
  - User: `trading_user`
  - Password: `trading_password_2025`
  - Database: `trading_bot`
- **Redis**: 
  - Password: `redis_password_2025`
- **pgAdmin**: 
  - Email: `admin@tradingbot.local`
  - Password: `admin_password_2025`

## 🛠️ Управление

### Основные команды
```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f backend

# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Пересборка
docker-compose build --no-cache
```

### Проверка состояния
```bash
# Статус контейнеров
docker-compose ps

# Использование ресурсов
docker stats

# Проверка здоровья
curl http://localhost:8000/health
```

## 🔍 Диагностика

### Backend не запускается
```bash
# Проверка логов
docker-compose logs backend

# Проверка зависимостей
docker-compose logs postgres redis

# Пересборка backend
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Проблемы с scikit-learn
Docker Dockerfile обновлен для решения проблем:
- Установка системных зависимостей (gcc, g++, BLAS, LAPACK)
- Поэтапная установка: numpy → scipy → scikit-learn
- Принудительная пересборка scikit-learn из исходников

### Проблемы с портами
```bash
# Проверка занятых портов
netstat -tlnp | grep :8000

# Остановка конфликтующих процессов
docker-compose down
sudo systemctl stop nginx  # если используется
```

## 📊 Мониторинг

### Веб-интерфейсы
- **API Docs**: http://localhost:8000/docs
- **Trading UI**: http://localhost:8000/trading-control
- **Health Check**: http://localhost:8000/health
- **pgAdmin**: http://localhost:8080

### Logs
```bash
# Все сервисы
docker-compose logs -f --tail=100

# Только ошибки
docker-compose logs -f | grep ERROR

# Конкретное время
docker-compose logs --since="2024-01-01T10:00:00" backend
```

## 🔄 Обновление

### Обновление кода
```bash
# Остановка
docker-compose down

# Пересборка
docker-compose build --no-cache

# Запуск
docker-compose up -d
```

### Обновление зависимостей
```bash
# Обновление requirements.txt
docker-compose build --no-cache backend

# Чистая установка
docker-compose down
docker system prune -f
docker-compose up -d --build
```

## 🆘 Решение проблем

### 1. Scikit-learn ImportError
**Решение**: Используйте Docker - проблема решена через изолированную Linux-среду

### 2. Порты заняты
```bash
# Найти процесс
sudo lsof -i :8000

# Убить процесс
sudo kill -9 <PID>
```

### 3. Нехватка памяти
```bash
# Увеличить лимиты в Docker Desktop
# Settings → Resources → Advanced → Memory: 8GB+
```

### 4. Проблемы с volumes
```bash
# Очистка volumes
docker-compose down -v
docker volume prune -f
```

## 🎯 Производительность

### Рекомендации
- **RAM**: 16GB для полного стека
- **CPU**: 4+ ядер для ML обработки
- **SSD**: Для быстрого доступа к БД
- **Docker Desktop**: Выделить 8GB+ RAM

### Оптимизация
```yaml
# В docker-compose.yml добавить:
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

## 🔒 Безопасность

### Продакшн настройки
- Изменить все пароли по умолчанию
- Использовать Docker secrets
- Настроить firewall правила
- Включить HTTPS

### Backup
```bash
# Backup PostgreSQL
docker exec trading_bot_postgres pg_dump -U trading_user trading_bot > backup.sql

# Backup volumes
docker run --rm -v trading_network_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

---

## 🎉 Результат

После успешного запуска у вас будет:
- ✅ Решена проблема с scikit-learn
- ✅ Полная изоляция окружения  
- ✅ Автоматические health checks
- ✅ Простое масштабирование
- ✅ Легкое развертывание на любой системе 