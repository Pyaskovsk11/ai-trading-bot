# 🚀 БЫСТРЫЙ СТАРТ - AI Trading Bot v2.0

## 🎯 РЕКОМЕНДУЕМАЯ СТРАТЕГИЯ: СБАЛАНСИРОВАННАЯ

**Лучшие результаты**: 52 сделки, 30.8% винрейт, -0.070% доходность

---

## ⚡ БЫСТРЫЙ ЗАПУСК (5 минут)

### 1. 🧪 Тестирование Сбалансированной Стратегии
```bash
python test_balanced_strategy.py
```

### 2. 🎯 Тестирование Консервативной Стратегии
```bash
python test_optimized_strategy.py
```

### 3. 📊 Полный Тест Системы
```bash
python test_final_system.py
```

---

## 🔧 НАСТРОЙКА ДЛЯ ПРОДАКШН

### 1. 📝 Создание .env файла
```bash
# Скопируйте и настройте
cp .env.example .env
```

### 2. ⚙️ Базовая конфигурация (.env)
```env
# Режим работы
SANDBOX=true
STRATEGY_PROFILE=MODERATE

# Капитал и риски
INITIAL_CAPITAL=1000
POSITION_SIZE=0.08
MAX_POSITIONS=5
MAX_DAILY_LOSS=0.02

# API ключи (настройте для реальной торговли)
BINGX_API_KEY=your_api_key
BINGX_SECRET_KEY=your_secret_key

# Telegram уведомления
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. 🚀 Запуск Реальной Торговли
```bash
# После настройки API ключей
python main.py --strategy=balanced
```

---

## 📊 ПРОФИЛИ СТРАТЕГИЙ

### 🥇 СБАЛАНСИРОВАННАЯ (Рекомендуется)
```python
STRATEGY_PROFILE=MODERATE
POSITION_SIZE=0.08        # 8% капитала
MAX_POSITIONS=5           # 5 одновременных позиций
SIGNAL_THRESHOLDS=40-28-18  # Сбалансированные пороги
```
**Результаты**: 52 сделки, 30.8% винрейт, -0.070% доходность

### 🛡️ КОНСЕРВАТИВНАЯ (Для начинающих)
```python
STRATEGY_PROFILE=CONSERVATIVE
POSITION_SIZE=0.06        # 6% капитала
MAX_POSITIONS=3           # 3 одновременных позиции
SIGNAL_THRESHOLDS=50-35-25  # Высокие пороги качества
```
**Результаты**: 15 сделок, 26.7% винрейт, -0.365% доходность, 0.933% просадка

### ⚡ АГРЕССИВНАЯ (Для опытных)
```python
STRATEGY_PROFILE=AGGRESSIVE
POSITION_SIZE=0.20        # 20% капитала
MAX_POSITIONS=8           # 8 одновременных позиций
SIGNAL_THRESHOLDS=30-20-12  # Низкие пороги
```
**Результаты**: 39 сделок, 10.3% винрейт, -0.701% доходность

---

## 🎯 ПОЭТАПНЫЙ ПЛАН ЗАПУСКА

### 📅 Неделя 1-2: Sandbox Тестирование
```bash
SANDBOX=true
INITIAL_CAPITAL=1000
STRATEGY_PROFILE=MODERATE
```
**Цель**: Проверить стабильность работы

### 📅 Неделя 3-6: Малый Капитал
```bash
SANDBOX=false
INITIAL_CAPITAL=500-2000
STRATEGY_PROFILE=CONSERVATIVE
```
**Цель**: Первый опыт реальной торговли

### 📅 Месяц 2-3: Масштабирование
```bash
INITIAL_CAPITAL=5000-20000
STRATEGY_PROFILE=MODERATE
```
**Цель**: Увеличение капитала при стабильных результатах

---

## 📊 МОНИТОРИНГ И КОНТРОЛЬ

### 🔍 Ключевые Метрики
- **Винрейт**: Цель >25%
- **Просадка**: Максимум 5%
- **Количество сделок**: 10-50 в неделю
- **Profit Factor**: Цель >0.8

### 📱 Уведомления
```bash
# Настройка Telegram бота
1. Создайте бота через @BotFather
2. Получите токен и chat_id
3. Добавьте в .env файл
```

### 🛑 Стоп-условия
- Просадка >5%
- 10 убыточных сделок подряд
- Технические ошибки

---

## 🔧 УСТРАНЕНИЕ ПРОБЛЕМ

### ❌ Ошибка API ключей
```bash
# Проверьте настройки в .env
python test_config_setup.py
```

### ❌ Нет сигналов
```bash
# Снизьте пороги сигналов
SIGNAL_THRESHOLDS=35-25-15
```

### ❌ Высокая просадка
```bash
# Уменьшите размер позиций
POSITION_SIZE=0.04
MAX_POSITIONS=3
```

---

## 📞 ПОДДЕРЖКА

### 📋 Логи
- **Основные**: `app/logs/trading.log`
- **Ошибки**: `app/logs/error.log`
- **Сделки**: `app/logs/trades.log`

### 🔧 Диагностика
```bash
# Проверка системы
python diagnostic_check.py

# Тест подключения к API
python test_api_connection.py
```

---

## 🎉 ГОТОВО!

**Система готова к работе. Начните с sandbox режима и постепенно переходите к реальной торговле.**

**Удачной торговли! 🚀📈** 