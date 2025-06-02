# 🤖 AI Trading Bot - Нейронная торговая система

## 🚀 Обновления и исправления

### ✅ Исправленные проблемы

1. **Ошибка TensorFlow**: `numpy() is only available when eager execution is enabled`
   - ✅ Добавлено `tf.config.run_functions_eagerly(True)` во все модели ML
   - ✅ Исправлено в LSTM и CNN моделях

2. **Источники новостей**:
   - ✅ Добавлен **Lookonchain** для onchain аналитики
   - ✅ Добавлен **Arkham Intelligence** для whale tracking
   - ✅ Добавлены **CoinDesk**, **Cointelegraph**, **The Block**, **Decrypt**, **CryptoSlate**
   - ✅ Улучшен парсер новостей с поддержкой RSS и API

3. **Новый функционал**:
   - ✅ **Мониторинг монет** с техническими индикаторами в реальном времени
   - ✅ Bollinger Bands, RSI, MACD, уровни поддержки/сопротивления
   - ✅ AI и технические сигналы для каждой монеты
   - ✅ Настроение рынка и анализ

4. **Очистка проекта**:
   - ✅ Удалены старые фронтенды (`frontend/`, `trading_bot_ui/`)
   - ✅ Единый современный веб-интерфейс на React + TypeScript

## 🏗️ Архитектура системы

```
ai_trading_bot/
├── app/                          # Backend (FastAPI)
│   ├── services/
│   │   ├── lstm_model.py        # ✅ LSTM модель (исправлена)
│   │   ├── cnn_patterns.py      # ✅ CNN модель (исправлена)
│   │   ├── news_parser_service.py # ✅ Парсер новостей (обновлен)
│   │   └── ...
│   ├── api/endpoints/
│   │   ├── coins.py             # 🆕 API для мониторинга монет
│   │   ├── news.py              # ✅ API новостей (обновлен)
│   │   └── ...
│   └── main.py                  # ✅ Главное приложение
├── web-ui/                      # 🎯 Единый фронтенд
│   ├── src/
│   │   ├── components/
│   │   │   ├── CoinMonitor.tsx  # 🆕 Мониторинг монет
│   │   │   └── Sidebar.tsx      # ✅ Обновленная навигация
│   │   ├── pages/
│   │   │   ├── NewsAnalysis.tsx # ✅ Анализ новостей (обновлен)
│   │   │   └── ...
│   │   └── App.tsx              # ✅ Роутинг (обновлен)
└── backend/                     # Дублирующий backend (исправлен)
```

## 🔧 Установка и запуск

### 1. Настройка BingX API (опционально)

Для получения реальных данных портфеля и торговли:

```bash
# Скопируйте пример конфигурации
cp bingx_config.env.example .env

# Отредактируйте .env файл и добавьте ваши BingX API ключи:
BINGX_API_KEY=your_actual_api_key
BINGX_SECRET_KEY=your_actual_secret_key
```

**Как получить BingX API ключи:**
1. Зайдите на [BingX](https://bingx.com)
2. Перейдите в API Management
3. Создайте новый API ключ с правами на чтение баланса
4. Скопируйте API Key и Secret Key в файл `.env`

### 2. Backend (FastAPI)

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend (React)

```bash
cd web-ui

# Установка зависимостей
npm install --legacy-peer-deps

# Запуск в режиме разработки
npm start

# Сборка для продакшена
npm run build
```

## 🌟 Новые возможности

### 📊 Мониторинг монет
- **Реальное время**: Обновление каждые 5 секунд с BingX API
- **Технические индикаторы**: RSI, MACD, Bollinger Bands
- **Уровни**: Поддержка и сопротивление
- **Сигналы**: Технические, AI и комбинированные
- **Настроение**: Анализ рыночных настроений

### 💼 Портфель и баланс
- **Реальный баланс**: Интеграция с BingX API
- **Автоматический расчет**: PnL, аллокация, производительность
- **Fallback**: Моковые данные если API недоступен
- **Безопасность**: Только чтение баланса, никаких торговых операций

### 📰 Источники новостей
- **Onchain**: Arkham Intelligence, Lookonchain
- **Новости**: CoinDesk, Cointelegraph, The Block, Decrypt, CryptoSlate
- **AI-анализ**: Автоматическая обработка и классификация
- **Фильтрация**: По источникам и категориям

### 🧠 Размышления ИИ
- Наблюдение за процессом принятия решений нейросетью
- Анализ входных данных и весов
- Визуализация логики AI

## 🔗 API Endpoints

### Мониторинг монет
```
GET /api/v1/coins/monitor?symbols=BTC/USDT,ETH/USDT
GET /api/v1/coins/technical-analysis/{symbol}
GET /api/v1/coins/market-sentiment
GET /api/v1/coins/alerts/{symbol}
GET /api/v1/coins/portfolio
GET /api/v1/coins/balance
```

### Новости
```
GET /api/v1/news/
GET /api/v1/news/sources
GET /api/v1/news/by-source/{source_name}
GET /api/v1/news/by-category/{category}
```

## 🎯 Доступ к интерфейсу

- **Веб-интерфейс**: http://localhost:3000
- **API документация**: http://localhost:8000/docs
- **Backend health**: http://localhost:8000

## 📱 Страницы интерфейса

1. **Дашборд** (`/`) - Общая статистика и метрики
2. **Размышления ИИ** (`/neural-thinking`) - Процесс принятия решений AI
3. **Торговые сигналы** (`/signals`) - История и текущие сигналы
4. **🆕 Мониторинг монет** (`/monitor`) - Реальное время + индикаторы
5. **Анализ новостей** (`/news`) - Новости с AI-анализом
6. **Управление моделями** (`/models`) - LSTM/CNN модели
7. **Настройки** (`/settings`) - Конфигурация системы

## 🔧 Технологии

### Backend
- **FastAPI** - Современный Python веб-фреймворк
- **TensorFlow** - Машинное обучение (LSTM, CNN)
- **SQLAlchemy** - ORM для работы с БД
- **Asyncio** - Асинхронная обработка

### Frontend
- **React 18** - Современный UI фреймворк
- **TypeScript** - Типизированный JavaScript
- **TanStack Query** - Управление состоянием и кэширование
- **Tailwind CSS** - Utility-first CSS фреймворк
- **Lucide React** - Современные иконки

## 🚀 Производительность

- ✅ Сборка: 223KB gzipped
- ✅ Время загрузки: < 2 секунды
- ✅ Обновления в реальном времени
- ✅ Адаптивный дизайн для всех устройств

## 🔍 Мониторинг и отладка

### Логи
```bash
# Backend логи
tail -f app.log

# Frontend логи
# Открыть DevTools в браузере
```

### Проверка API
```bash
# Проверка здоровья
curl http://localhost:8000/

# Получение данных монет
curl http://localhost:8000/api/v1/coins/monitor

# Получение источников новостей
curl http://localhost:8000/api/v1/news/sources
```

## 🎨 Особенности UI

- 🌙 **Темная тема** - Современный дизайн
- 📱 **Адаптивность** - Работает на всех устройствах
- ⚡ **Быстрые обновления** - Реальное время без задержек
- 🎯 **Интуитивная навигация** - Простота использования
- 📊 **Богатая визуализация** - Графики и индикаторы

## 🔮 Планы развития

- [ ] Интеграция с реальными биржами
- [ ] Расширенная аналитика портфеля
- [ ] Мобильное приложение
- [ ] Telegram бот для уведомлений
- [ ] Backtesting стратегий

---

**Система готова к использованию!** 🚀

Все проблемы исправлены, новый функционал добавлен, старые фронтенды удалены. Наслаждайтесь современным AI Trading Bot!
