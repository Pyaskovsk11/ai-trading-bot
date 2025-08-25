# 🤖 AI Trading Bot

**Интеллектуальная система автоматической торговли криптовалютами с использованием искусственного интеллекта и мульти-агентной архитектуры.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

## 🚀 Возможности

- **🤖 Мульти-агентная архитектура** с использованием PraisonAI
- **📊 Технический анализ** (RSI, MACD, Bollinger Bands, Volume)
- **🎯 Управление рисками** с динамическими стоп-лоссами и тейк-профитами
- **📈 Бэктестинг** на исторических данных
- **🔔 Уведомления** через Telegram
- **🌐 Веб-интерфейс** для мониторинга
- **📱 Интеграция с BingX API** для реальной торговли
- **📊 Мониторинг производительности** в реальном времени
- **🎨 Современный лендинг** с мультиязычной поддержкой

## 🏗️ Архитектура

### Основные компоненты:

1. **Market Analyzer Agent** - Анализ рыночных данных
2. **Risk Manager Agent** - Управление рисками
3. **Signal Generator Agent** - Генерация торговых сигналов
4. **News Analyzer Agent** - Анализ новостей
5. **Portfolio Manager Agent** - Управление портфелем
6. **Execution Manager Agent** - Исполнение сделок

### Технологический стек:

- **Backend**: Python 3.8+, FastAPI, SQLAlchemy
- **AI Framework**: PraisonAI (Multi-Agent System)
- **Database**: PostgreSQL
- **Trading API**: BingX
- **Notifications**: Telegram Bot API
- **Frontend**: React.js
- **Deployment**: Docker

## 📦 Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/ai-trading-bot.git
cd ai-trading-bot
```

### 2. Установка зависимостей

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../web-ui
npm install
```

### 3. Настройка переменных окружения

```bash
# Скопируйте пример файла
cp backend/env.example backend/.env

# Отредактируйте .env файл
nano backend/.env
```

**Необходимые переменные:**
```env
# OpenAI API
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.openai.com/v1

# BingX API
BINGX_API_KEY=your_bingx_api_key
BINGX_API_SECRET=your_bingx_api_secret
TESTNET=true

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Database
DATABASE_URL=postgresql://user:password@localhost/ai_trading_bot
```

### 4. Запуск с Docker

```bash
# Запуск всех сервисов
docker-compose up -d

# Или запуск только backend
cd backend
docker build -t ai-trading-bot .
docker run -p 8000:8000 ai-trading-bot
```

## 🚀 Быстрый старт

### 1. Запуск гибридной системы (рекомендуется)

```bash
cd backend
python start_hybrid_system.py
```

### 2. Запуск полной интегрированной системы

```bash
cd backend
python start_full_integrated_system.py
```

### 3. Запуск бэктестинга

```bash
cd backend
python backtest_optimized.py
```

### 4. Запуск веб-интерфейса

```bash
cd web-ui
npm start
```

## 📊 Бэктестинг

Система включает несколько стратегий бэктестинга:

- `backtest_system.py` - Базовая стратегия
- `backtest_aggressive.py` - Агрессивная стратегия
- `backtest_optimized.py` - Оптимизированная стратегия
- `backtest_balanced.py` - Сбалансированная стратегия
- `backtest_final.py` - Финальная стратегия

### Пример запуска:

```bash
cd backend
python backtest_optimized.py
```

## 🔧 Конфигурация

### Настройка агентов

Файл конфигурации: `backend/config/praisonai_agents.yaml`

```yaml
market_analyzer:
  role: "Market Data Analyst"
  goal: "Analyze market trends and identify opportunities"
  backstory: "Expert in technical analysis and market dynamics"
  
risk_manager:
  role: "Risk Management Specialist"
  goal: "Evaluate and manage trading risks"
  backstory: "Experienced risk manager with deep understanding of market volatility"
```

### Настройка стратегии

Основные параметры в файлах бэктестинга:

```python
strategy_params = {
    'rsi_period': 14,
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'position_size_pct': 0.02,
    'stop_loss_pct': 0.02,
    'take_profit_pct': 0.08,
    'max_positions': 2,
    'max_daily_trades': 2
}
```

## 📈 Мониторинг

### Веб-интерфейс

Доступен по адресу: `http://localhost:3000`

### Telegram уведомления

Настройте бота в Telegram для получения уведомлений о:
- Торговых сигналах
- Открытии/закрытии позиций
- Отчетах о производительности
- Системных ошибках

### Логи

Логи сохраняются в директории `backend/logs/`:
- `praisonai_production.log` - Основные логи системы
- `backtest_*.log` - Логи бэктестинга
- `trading_*.log` - Логи торговли

## 🧪 Тестирование

### Запуск тестов

```bash
cd backend
python -m pytest tests/
```

### Тестирование API

```bash
cd backend
python test_real_api.py
```

### Диагностика системы

```bash
cd backend
python diagnose_system.py
```

## 📁 Структура проекта

```
ai-trading-bot/
├── backend/                 # Основной код системы
│   ├── app/                # Основное приложение
│   ├── config/             # Конфигурационные файлы
│   ├── logs/               # Логи системы
│   ├── tests/              # Тесты
│   └── *.py               # Основные скрипты
├── landing/                 # Современный лендинг
│   ├── app/                # Next.js приложение
│   ├── components/         # React компоненты
│   ├── messages/           # Мультиязычные переводы
│   └── *.ps1              # PowerShell скрипты
├── web-ui/                 # Веб-интерфейс
├── docs/                   # Документация
├── docker/                 # Docker конфигурация
├── alembic/               # Миграции базы данных
└── README.md              # Этот файл
```

## 🌐 Лендинг

Современный мультиязычный лендинг с красивыми анимациями и адаптивным дизайном.

### Быстрый запуск

```powershell
cd landing
.\start-landing.ps1
```

### Ручной запуск

```powershell
cd landing
npm install
npm run dev
```

### Доступные URL

- **Корневой**: `http://localhost:3000` (автоматический редирект на `/en`)
- **Английский**: `http://localhost:3000/en`
- **Русский**: `http://localhost:3000/ru`

### Технологии лендинга

- **Next.js 14** - React фреймворк
- **TypeScript** - Типизированный JavaScript
- **Tailwind CSS** - Utility-first CSS фреймворк
- **Framer Motion** - Анимации
- **next-intl** - Интернационализация

## 🔒 Безопасность

- Все API ключи хранятся в переменных окружения
- Поддержка тестового режима (testnet)
- Валидация всех входных данных
- Логирование всех операций

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/your-username/ai-trading-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/ai-trading-bot/discussions)
- **Email**: support@ai-trading-bot.com

## ⚠️ Отказ от ответственности

Этот проект предназначен только для образовательных целей. Торговля криптовалютами связана с высокими рисками. Авторы не несут ответственности за любые финансовые потери.

## 🏆 Статус проекта

- ✅ Мульти-агентная архитектура
- ✅ Интеграция с BingX API
- ✅ Система бэктестинга
- ✅ Telegram уведомления
- ✅ Веб-интерфейс
- ✅ Docker поддержка
- ✅ Современный лендинг
- 🔄 Постоянные улучшения

---

**Сделано с ❤️ для сообщества трейдеров** 