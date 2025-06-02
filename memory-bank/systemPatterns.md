# System Patterns

## Architecture Overview

Образовательная платформа с AI персонализацией и freemium моделью

```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Landing Page  │◄─►│ Auth System   │◄─►│ User Dashboard│
└───────────────┘    └───────────────┘    └───────────────┘
        │                   │                    │
        ▼                   ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Learning Hub  │    │ AI Signals    │    │ Portfolio     │
└───────────────┘    └───────────────┘    └───────────────┘
        │                   │                    │
        ▼                   ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ AI Coach      │    │ Subscription  │    │ Gamification  │
│ "Alex"        │    │ Management    │    │ System        │
└───────────────┘    └───────────────┘    └───────────────┘
```

## Key Design Patterns

### 1. User-Centric Design
- **Progressive disclosure**: Показываем функции по мере роста опыта пользователя
- **Personalization**: AI адаптирует контент под профиль и прогресс
- **Freemium gates**: Естественные точки конверсии в платные планы
- **Gamification**: Мотивация через достижения, уровни, прогресс

### 2. AI-First Approach  
- **AI Coach "Alex"**: Персональный ментор с человеческой личностью
- **Explainable signals**: Каждое AI решение объясняется простым языком
- **Adaptive learning**: Система подстраивается под темп и стиль обучения
- **Context awareness**: AI понимает уровень пользователя и дает релевантные советы

### 3. Educational Framework
- **Structured learning paths**: От новичка до эксперта через четкие этапы  
- **Practice-first**: Виртуальное портфолио без рисков для отработки навыков
- **Micro-learning**: Короткие уроки 5-10 минут для лучшего усвоения
- **Community support**: Peer learning и менторство между пользователями

### 4. Content Management
- **Modular lessons**: Независимые блоки знаний с четкими learning outcomes
- **Interactive elements**: Квизы, симуляторы, практические задания
- **Progress tracking**: Детальная аналитика обучения для мотивации
- **Certification system**: Признание достижений через цифровые сертификаты

### 5. Business Model Integration
- **Value-based tiers**: Каждый план решает конкретные проблемы пользователя
- **Natural upgrades**: Функции следующего уровня становятся очевидной потребностью
- **Retention focus**: Долгосрочная ценность важнее быстрой конверсии
- **Community network effects**: Пользователи приводят друзей через реферальную программу

### 6. Technical Architecture
- **Mobile-first responsive**: Обучение на любых устройствах
- **Offline capabilities**: Загрузка контента для обучения без интернета
- **Real-time updates**: Мгновенные уведомления о новых сигналах
- **API-driven**: Возможность интеграции с внешними системами

## Data Flow Patterns

### 1. User Journey Flow
```
Registration → Onboarding → Learning Path → Practice → Real Trading → Mastery
     ↓             ↓            ↓           ↓           ↓          ↓
 Email/Social → Profile Setup → Lessons → Virtual → Signals → Advanced
 Verification   Goals/Risk     Quizzes   Portfolio  Following   Strategies
```

### 2. AI Personalization Flow
```
User Data → AI Analysis → Content Adaptation → Delivery → Feedback → Refinement
    ↓           ↓              ↓              ↓          ↓          ↓
 Behavior   Learning    Difficulty Level   Lesson     Progress   Next Level
 Tracking   Style Det.   Adjustment       Selection   Tracking   Suggestion
```

### 3. Signal Generation Flow
```
Market Data → AI Analysis → Signal → Explanation → User Alert → Tracking
     ↓           ↓           ↓          ↓           ↓          ↓
  Real-time   Technical   Entry/Exit  Why/How   Telegram    Results
   Feeds      +News       Levels      It Works   +Email     Analytics
```

### 4. Monetization Flow
```
Free User → Value Demo → Pain Point → Upgrade Prompt → Payment → Premium Features
    ↓          ↓           ↓             ↓             ↓           ↓
 Limited    Show What   Hit Limit    Offer Solution  Stripe    Full Access
 Access     They Miss   Or Need      With Benefit   Process   +Support
```

## Component Architecture

### 1. Frontend Components Structure
```
src/
├── pages/
│   ├── public/              # Landing, Pricing, About
│   ├── auth/                # Login, Register, Onboarding
│   ├── dashboard/           # User Dashboard, Profile
│   ├── learning/            # Lessons, Quizzes, Certificates
│   ├── signals/             # AI Signals, History
│   ├── portfolio/           # Virtual/Real Portfolio
│   └── subscription/        # Billing, Payment
├── components/
│   ├── common/              # Shared UI components
│   ├── ai-coach/            # Alex chat interface
│   ├── charts/              # Trading charts
│   └── gamification/        # Progress, Achievements
└── services/
    ├── api/                 # API integration
    ├── auth/                # Authentication
    └── ai/                  # AI/OpenAI integration
```

### 2. Backend Services Structure
```
backend/
├── api/
│   ├── auth/                # User authentication
│   ├── users/               # User management
│   ├── learning/            # Course content
│   ├── signals/             # AI trading signals
│   ├── portfolio/           # Portfolio management
│   └── payments/            # Stripe integration
├── services/
│   ├── ai_coach/            # OpenAI integration
│   ├── signals_engine/      # Signal generation
│   ├── analytics/           # User analytics
│   └── notifications/       # Email/Telegram
└── models/
    ├── user/                # User data models
    ├── learning/            # Educational content
    └── trading/             # Trading related data
```

### 3. Database Schema Patterns
```
Users ←→ UserProfiles ←→ LearningProgress ←→ Achievements
  ↓         ↓               ↓                   ↓
Subscriptions ←→ Lessons ←→ Quizzes ←→ Certificates
  ↓              ↓          ↓           ↓
Payments ←→ Signals ←→ Portfolio ←→ TradingHistory
```

## Security & Privacy Patterns

### 1. User Data Protection
- **Minimal data collection**: Только необходимые данные для персонализации
- **GDPR compliance**: Право на забвение и портируемость данных
- **Encryption**: Все персональные данные зашифрованы
- **API security**: Rate limiting, authentication, input validation

### 2. Payment Security
- **PCI compliance**: Через Stripe - не храним карточные данные
- **Fraud detection**: Мониторинг подозрительных транзакций
- **Subscription security**: Защита от несанкционированных изменений тарифов

### 3. Content Security
- **Plagiarism protection**: Водяные знаки, tracking просмотров
- **Access control**: Строгое разграничение прав по тарифным планам
- **API throttling**: Защита от злоупотребления API доступом

## Scalability Patterns

### 1. Performance Optimization
- **CDN delivery**: Статический контент через CDN
- **Lazy loading**: Загрузка контента по требованию
- **Caching strategy**: Redis для часто запрашиваемых данных
- **Database optimization**: Индексы, query optimization

### 2. Infrastructure Scaling
- **Microservices ready**: Каждый сервис может масштабироваться независимо
- **Container deployment**: Docker для простого развертывания
- **Load balancing**: Распределение нагрузки между инстансами
- **Auto-scaling**: Автоматическое масштабирование по нагрузке

### 3. Content Scaling
- **Modular content**: Новые курсы добавляются без изменения кода
- **Internationalization**: Готовность к переводу на другие языки
- **White-label ready**: Возможность брендинга для партнеров
