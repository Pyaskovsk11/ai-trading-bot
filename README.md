<<<<<<< HEAD
# AI Futures Trading Bot

## Быстрый старт

### 1. Клонирование и установка зависимостей
```powershell
git clone <repo_url>
cd ai_trading_bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install fastapi sqlalchemy psycopg2-binary
```

### 2. Настройка переменных окружения
Создайте файл `.env` на основе `.env.example` и укажите параметры БД, Telegram и др.

### 3. Миграции БД
```powershell
alembic upgrade head
```

### 4. Запуск backend
```powershell
uvicorn app.main:app --reload
```

### 5. Запуск тестов
```powershell
pytest --cov=app
```

### 6. Запуск Telegram-бота
```powershell
python telegram_bot/bot.py
```

### 7. CI/CD
Тесты автоматически запускаются при каждом push/pull request (см. .github/workflows/ci.yml).

---

## Структура проекта
- `app/` — backend (FastAPI)
- `telegram_bot/` — Telegram-бот
- `webapp/` — frontend (React)
- `tests/` — тесты (unit, integration, e2e)
- `Docs/` — документация

## Документация API
Swagger: http://localhost:8000/docs

---

## Контакты и поддержка
Вопросы — в Issues или Telegram. 
=======
# ai-trading-bot
My step to success
>>>>>>> 515004a9685bc397c1bac403b62d654dc51a8b6a
