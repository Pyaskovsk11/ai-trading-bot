# System Patterns

## Architecture Overview

Гибридная архитектура: Explainable AI + Event-driven ядро (inspired by Nautilus Trader)

```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Web/Telegram  │◄─►│ Event Bus     │◄─►│  AI/ML Engine │
└───────────────┘    └───────────────┘    └───────────────┘
        │                   │                    │
        ▼                   ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Risk Manager  │    │ Execution     │    │ Logger/Monitor│
└───────────────┘    └───────────────┘    └───────────────┘
        │                   │                    │
        ▼                   ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Plugins:      │    │ Backtester    │    │ Data Sources  │
│ Strategies    │    │ (event replay)│    │ (live/hist)   │
└───────────────┘    └───────────────┘    └───────────────┘
```

## Key Design Patterns

### 1. Event-driven Core
- Event bus (pub/sub): все сервисы общаются через события
- Каждый сервис — подписчик/публикатор событий (AI, Risk, Execution, Telegram, Logger)
- Легко добавлять новые сервисы и плагины

### 2. Plugins & Modularity
- Стратегии, risk-алгоритмы, источники данных — плагины
- Горячая замена/добавление без остановки ядра

### 3. Backtesting & Simulation
- Event replay: симуляция исполнения сигналов на истории
- Учёт latency, slippage, комиссий, ошибок исполнения
- Сравнение стратегий и risk-алгоритмов в едином фреймворке

### 4. Monitoring & Profiling
- Сбор метрик latency, throughput, PnL, drawdown, coverage
- Профилирование узких мест
- Алерты и отчёты через Telegram/web

### 5. Explainable AI Integration
- AI/ML/RAG/XAI сервисы публикуют explainable сигналы и объяснения
- Risk Manager и Execution используют AI confidence и explainability
- Telegram/web получают объяснения и алерты через event bus

## Data Flow

1. Market Data/News → Event Bus → AI/ML → Signal Event → Risk → Execution → Order Event
2. User/Web → Event Bus → Settings/Commands → System Adaptation
3. Trade Events → Event Bus → Logger/Monitor → Telegram/Alerts
4. Backtest: Исторические события → Event Bus → все сервисы (replay)

## Security & Scalability Patterns
- API Security, Key Security, Async/Await, Modular Design, Configuration as Code, CI/CD