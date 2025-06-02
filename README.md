# AI Trading Academy & Signals 🎓🤖

> **Образовательная платформа для криптотрейдинга с персональным AI-коучем и готовыми торговыми сигналами**

## 🎯 О проекте

AI Trading Academy & Signals - это современная образовательная платформа, которая помогает новичкам и опытным трейдерам изучать криптотрейдинг безопасно и эффективно. Платформа предоставляет структурированное обучение, персональный AI-коуч "Alex" и готовые торговые сигналы с объяснениями.

### ✨ Ключевые особенности

- **🤖 AI Coach "Alex"** - персональный ментор с дружелюбной личностью
- **📚 Структурированное обучение** - от новичка до профессионала
- **💡 Explainable AI** - каждый сигнал объясняется простым языком  
- **📊 Виртуальное портфолио** - практика без финансовых рисков
- **💎 Freemium модель** - бесплатный старт с возможностью upgrade
- **📱 Mobile-first дизайн** - обучение на любых устройствах

## 🎯 Целевая аудитория

### 🟢 **Primary: Crypto Beginners (70%)**
- Возраст: 25-45 лет, доход $50K-150K/год
- Слышали о крипте, но боятся торговать
- Нужно безопасное обучение с поддержкой

### 🟡 **Secondary: Struggling Traders (25%)**  
- Уже торгуют 6+ месяцев, потеряли деньги
- Хотят улучшить навыки и найти надежные сигналы

### 🔵 **Tertiary: Advanced Traders (5%)**
- Опытные трейдеры, ищут дополнительные источники альфы
- Готовы платить за качественные алгоритмические сигналы

## 💰 Бизнес-модель

| План | Цена | Возможности |
|------|------|-------------|
| **🆓 Free** | Бесплатно | 3 урока/неделю, 5 сигналов/день, виртуальное портфолио |
| **💎 Premium** | $29/мес | Безлимитное обучение, все сигналы, Telegram уведомления |
| **🏆 Pro** | $99/мес | Персональный AI коуч, API доступ, закрытые вебинары |

## 🏗️ Архитектура платформы

### 📱 Frontend (React 18 + TypeScript)
```
src/
├── pages/
│   ├── public/          # Landing, Pricing, About
│   ├── auth/            # Login, Register, Onboarding
│   ├── dashboard/       # User Dashboard
│   ├── learning/        # Educational content
│   ├── signals/         # AI Trading signals
│   ├── portfolio/       # Portfolio management
│   └── subscription/    # Payment & billing
├── components/
│   ├── common/          # Shared UI components
│   ├── ai-coach/        # Alex chat interface
│   └── gamification/    # Progress, achievements
└── services/
    ├── api/             # API integration
    ├── auth/            # Authentication
    └── ai/              # AI integrations
```

### 🔧 Backend (FastAPI + Python)
```
backend/
├── api/
│   ├── auth/            # Authentication endpoints
│   ├── users/           # User management
│   ├── learning/        # Course content API
│   ├── signals/         # Trading signals API
│   └── payments/        # Stripe integration
├── services/
│   ├── ai_coach/        # OpenAI service
│   ├── signals_engine/  # Signal generation
│   └── notifications/   # Email/Telegram
└── models/              # Database models
```

## 🛠️ Технологический стек

### Frontend
- **React 18** + TypeScript
- **TailwindCSS** для стилизации
- **React Query** для state management
- **LightweightCharts** для графиков

### Backend  
- **FastAPI** + Python 3.9+
- **OpenAI API** для AI Coach
- **PostgreSQL** для данных
- **Redis** для кэширования
- **Stripe** для платежей

### Infrastructure
- **Docker** для контейнеризации
- **Vercel** для frontend deploy
- **Railway** для backend deploy
- **Telegram Bot** для уведомлений

## 🚀 Быстрый старт

### Предварительные требования
- Python 3.9+
- Node.js 16+
- PostgreSQL
- Redis

### Установка

1. **Клонируйте репозиторий**
```bash
git clone https://github.com/yourusername/ai-trading-academy.git
cd ai-trading-academy
```

2. **Backend setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Frontend setup**
```bash
cd web-ui
npm install
```

4. **Environment variables**
```bash
# Copy example files
cp database.env.example database.env
cp bingx_config.env.example bingx_config.env

# Edit with your values
DATABASE_URL=postgresql://user:pass@localhost/trading_academy_db
OPENAI_API_KEY=your_openai_api_key
STRIPE_SECRET_KEY=sk_test_...
```

5. **Запуск**
```bash
# Backend
cd backend && python working_main.py

# Frontend
cd web-ui && npm start
```

Откройте http://localhost:3001 в браузере.

## 📊 Roadmap разработки

### Phase 1: MVP Core (2-3 недели) ✅
- [x] Landing Page с регистрацией
- [x] Basic Dashboard  
- [x] Simple Learning (5 базовых уроков)
- [x] Mock AI Signals
- [x] Virtual Portfolio
- [x] Payment Integration (Stripe)

### Phase 2: AI Integration (1 месяц) 🔄
- [ ] OpenAI API интеграция
- [ ] Real AI Signals System
- [ ] Telegram Bot для уведомлений
- [ ] Персонализация контента
- [ ] Mobile Responsive Design

### Phase 3: Advanced Features (1 месяц) 📋
- [ ] Advanced Analytics
- [ ] Exchange API Integration
- [ ] Community Features
- [ ] Gamification System
- [ ] Advanced Learning Content

## 📈 Success Metrics

### Acquisition
- 100+ регистраций в первую неделю
- 50%+ completion rate onboarding
- 40%+ daily active users

### Engagement  
- 70%+ completion rate первого урока
- 3+ уроков в среднем на пользователя
- 60%+ return rate на следующий день

### Monetization
- 10%+ conversion в Premium план
- 2%+ conversion в Pro план
- $500+ MRR к концу первого месяца

## 🤝 Contributing

Мы приветствуем вклад сообщества! Пожалуйста:

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. [LICENSE](LICENSE) файл для деталей.

## 📞 Контакты

- **Email**: support@tradingacademy.ai
- **Telegram**: @tradingacademybot
- **Website**: https://tradingacademy.ai

---

**🚀 Готов изменить мир криптотрейдинга через образование и AI!** 