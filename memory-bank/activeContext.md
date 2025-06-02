# Active Context

## Текущий Фокус: Архитектурное Переосмысление Проекта 🎯 В ПРОЦЕССЕ

**Статус**: КАРДИНАЛЬНАЯ ПЕРЕРАБОТКА - Переход от технической торговой платформы к образовательной AI Trading Academy & Signals

### 🎯 Философский Поворот Проекта

#### **От чего уходим:**
- ❌ Сложная техническая платформа для разработчиков
- ❌ Event-driven архитектура с плагинами  
- ❌ Промышленный бэктестинг и квантовые стратегии
- ❌ Интерфейс для программистов и опытных трейдеров
- ❌ Фокус на технологиях, а не на пользователе

#### **К чему идем:**
- ✅ Образовательная платформа для массового рынка
- ✅ AI Trading Academy & Signals концепция
- ✅ Freemium модель с подписками
- ✅ Персонализированное обучение с AI коучем "Alex"
- ✅ Focus на пользовательский опыт и простоту

### 🏗️ Новая Архитектура Приложения

#### **📱 Структура сайта (8 основных разделов):**

1. **🏠 ПУБЛИЧНЫЕ СТРАНИЦЫ**
   - Landing Page (/) - продающая главная с hero, проблемы, решения
   - Pricing Page (/pricing) - детальное сравнение тарифов 
   - About Page (/about) - о команде и миссии

2. **🔐 АВТОРИЗАЦИЯ**  
   - Register Page (/register) - простая регистрация
   - Login Page (/login) - быстрый вход
   - Onboarding (/onboarding) - персонализация (4 шага)

3. **📊 DASHBOARD**
   - Dashboard Page (/dashboard) - персонализированный хаб
   - Profile Page (/profile) - настройки профиля
   - Settings Page (/settings) - общие настройки

4. **🎓 ОБУЧЕНИЕ**
   - Learning Page (/learning) - курсы и треки
   - Lesson Page (/learning/lesson/:id) - интерактивные уроки
   - Quiz Page (/learning/quiz/:id) - тесты и задания
   - Certificate Page (/learning/certificate/:id) - сертификаты

5. **🤖 AI СИГНАЛЫ**
   - Signals Page (/signals) - актуальные торговые сигналы
   - Signal Details (/signals/:id) - детальный анализ сигнала
   - Signal History (/signals/history) - история эффективности

6. **💼 ПОРТФОЛИО** 
   - Portfolio Page (/portfolio) - управление инвестициями
   - Analytics Page (/portfolio/analytics) - глубокая аналитика
   - Trade History (/portfolio/history) - история сделок

7. **💳 ПОДПИСКА**
   - Subscription Page (/subscription) - управление тарифом
   - Payment Page (/payment) - обработка платежей
   - Billing History (/billing) - история платежей

8. **🎮 GAMIFICATION** (будущее)
   - Achievements (/achievements) - достижения и бейджи
   - Leaderboard (/leaderboard) - рейтинги пользователей
   - Challenges (/challenges) - еженедельные челленджи

### 🎨 Дизайн-Система и UX Принципы

#### **Визуальный Стиль:**
- **Цветовая палитра**: Темная тема с синими/зелеными акцентами
- **Типографика**: Inter для текста, JetBrains Mono для кода
- **Компоненты**: Минималистичные, функциональные карточки
- **Анимации**: Плавные переходы, ненавязчивые

#### **UX Принципы:**
- **Простота**: Каждая страница = одна цель
- **Прогресс**: Визуализация обучения и достижений  
- **Доверие**: Прозрачность AI решений и статистики
- **Геймификация**: Мотивация через уровни и достижения

#### **AI Персонаж "Alex":**
- **Личность**: Дружелюбный ментор, не снобистский
- **Стиль общения**: Объясняет сложное простыми словами
- **Фразы**: "Давайте разберем этот сигнал", "Отличная сделка!"
- **Присутствие**: На всех ключевых экранах с контекстными советами

### 💰 Бизнес-Модель (Freemium)

#### **🆓 Free Tier:**
- 3 урока в неделю
- 5 AI сигналов в день  
- Виртуальное портфолио
- Базовая аналитика
- Комьюнити доступ

#### **💎 Premium ($29/месяц):**
- Безлимитное обучение
- Все AI сигналы
- Telegram уведомления
- Продвинутая аналитика
- Приоритетная поддержка

#### **🏆 Pro ($99/месяц):**
- Персональный AI коуч
- Индивидуальные стратегии
- API для автоторговли  
- Закрытые вебинары
- Ранний доступ к новым фичам

### 🛠️ Технический Stack (Updated)

#### **Frontend:**
- React 18 + TypeScript
- TailwindCSS для стилизации
- React Query для state management
- React Router для навигации
- LightweightCharts для графиков

#### **Backend:**  
- FastAPI + Python 3.9+
- OpenAI API для AI функций
- PostgreSQL для пользовательских данных
- Redis для кэширования
- Stripe для платежей

#### **Infrastructure:**
- Docker для containerization
- Vercel/Netlify для frontend deploy
- Railway/Render для backend deploy
- Telegram Bot API для уведомлений

### 📋 План Реализации (MVP в 3 фазы)

#### **Phase 1: MVP Core (2-3 недели)**
- ✅ Landing Page с регистрацией
- ✅ Basic Dashboard
- ✅ Simple Learning (5 базовых уроков)
- ✅ Mock AI Signals (без реального AI)
- ✅ Virtual Portfolio
- ✅ Payment Integration (Stripe)

#### **Phase 2: AI Integration (1 месяц)**  
- ✅ OpenAI API интеграция
- ✅ Real AI Signals System  
- ✅ Telegram Bot для уведомлений
- ✅ Персонализация контента
- ✅ Mobile Responsive Design

#### **Phase 3: Advanced Features (1 месяц)**
- ✅ Advanced Analytics
- ✅ Exchange API Integration  
- ✅ Community Features
- ✅ Gamification System
- ✅ Advanced Learning Content

### 🎯 Текущие Действия

#### **Немедленные Задачи:**
1. **Обновить Memory Bank** ✅ В ПРОЦЕССЕ
2. **Создать Landing Page** - начать с hero секции
3. **Настроить новую структуру маршрутов** в React Router
4. **Создать дизайн-систему** компонентов
5. **Переписать API endpoints** под новую логику

#### **На этой неделе:**
- [ ] Завершить архитектуру всех 8 разделов  
- [ ] Создать Landing Page MVP
- [ ] Настроить authentication flow
- [ ] Создать базовый Dashboard
- [ ] Подключить OpenAI API для MVP Alex

#### **На следующей неделе:**
- [ ] Создать Learning Center с первыми уроками
- [ ] Реализовать Signal System MVP
- [ ] Интегрировать Stripe платежи
- [ ] Создать виртуальное портфолио
- [ ] Telegram Bot setup

### 🏆 Ожидаемые Результаты

#### **Метрики Успеха MVP:**
- 100+ регистраций в первую неделю
- 70%+ completion rate первого урока  
- 10%+ conversion в Premium план
- 4.5+ рейтинг пользовательского опыта
- 60%+ daily/weekly retention

#### **Business Impact:**
- Переход от B2B/developer фокуса к B2C/mass market
- Scalable revenue model через подписки
- Viral growth potential через community
- Possible exit strategy (acquisition/IPO)

### 🚀 Готовность к Следующему Этапу

**Архитектура проработана на 90%** - готов начать имплементацию с любой страницы. Рекомендую начать с **Landing Page**, так как она определит tone of voice и общее восприятие продукта.

**Memory Bank обновлен** с новой концепцией - можно начинать разработку! 🎉
