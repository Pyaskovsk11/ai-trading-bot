# Tech Context

## Core Technologies Stack

### Frontend Framework
- **React 18** — Современный UI framework с hooks и concurrent features
- **TypeScript** — Type safety и better developer experience
- **TailwindCSS** — Utility-first CSS framework для быстрой разработки
- **React Router v6** — Client-side routing для SPA
- **React Query** — Server state management и caching

### AI & Learning Platform
- **OpenAI API (GPT-4)** — AI Coach "Alex" и content generation  
- **LangChain** — AI workflows и prompt engineering
- **Pinecone/Weaviate** — Vector database для similarity search
- **sentence-transformers** — Content embeddings для персонализации
- **scikit-learn** — Basic ML для user behavior analysis

### Backend Framework
- **FastAPI** — Высокопроизводительный async веб-фреймворк
- **Pydantic v2** — Data validation и API schemas
- **SQLAlchemy** — ORM для работы с базой данных
- **Alembic** — Database migrations management
- **Celery + Redis** — Background tasks и message broker

### Authentication & Payments
- **NextAuth.js / Auth0** — Аутентификация через соцсети и email
- **Stripe API** — Payment processing и subscription management
- **JWT tokens** — Stateless authentication
- **bcrypt** — Password hashing
- **OAuth2** — Social login (Google, Facebook, Twitter)

### Database & Storage
- **PostgreSQL 15+** — Primary database с JSON support
- **Redis 7+** — Caching, sessions, queue management
- **AWS S3 / Cloudinary** — File storage для images/videos
- **Elasticsearch** — Full-text search для content
- **Backup automation** — Daily automated backups

### Communications & Notifications
- **Telegram Bot API** — Real-time уведомления о сигналах
- **SendGrid / Mailgun** — Email notifications и marketing
- **WebSockets** — Real-time updates в web interface
- **Push notifications** — Browser push для важных events

### Monitoring & Analytics
- **Sentry** — Error tracking и performance monitoring
- **Google Analytics 4** — User behavior tracking
- **Mixpanel / Amplitude** — Product analytics
- **DataDog / New Relic** — Infrastructure monitoring
- **Custom dashboards** — Business metrics tracking

## Development Setup

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/trading_academy_db
REDIS_URL=redis://localhost:6379

# AI Services
OPENAI_API_KEY=your_openai_api_key
LANGCHAIN_API_KEY=your_langchain_key
PINECONE_API_KEY=your_pinecone_key

# Authentication
NEXTAUTH_SECRET=your_nextauth_secret
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Payments
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Communications
TELEGRAM_BOT_TOKEN=your_bot_token
SENDGRID_API_KEY=your_sendgrid_key

# Storage
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
S3_BUCKET_NAME=trading-academy-assets

# Monitoring
SENTRY_DSN=your_sentry_dsn
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
```

### Project Structure (New Architecture)
```
trading-academy/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── public/           # Landing, Pricing, About
│   │   │   ├── auth/             # Login, Register, Onboarding
│   │   │   ├── dashboard/        # User Dashboard
│   │   │   ├── learning/         # Educational content
│   │   │   ├── signals/          # AI Trading signals
│   │   │   ├── portfolio/        # Portfolio management
│   │   │   └── subscription/     # Payment & billing
│   │   ├── components/
│   │   │   ├── common/           # Shared components
│   │   │   ├── ai-coach/         # Alex chat interface
│   │   │   ├── charts/           # Trading charts
│   │   │   └── gamification/     # Progress, achievements
│   │   ├── services/
│   │   │   ├── api/              # API client
│   │   │   ├── auth/             # Authentication
│   │   │   └── ai/               # AI integrations
│   │   └── utils/
│   ├── public/
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth/             # Authentication endpoints
│   │   │   ├── users/            # User management
│   │   │   ├── learning/         # Course content API
│   │   │   ├── signals/          # Trading signals API  
│   │   │   ├── portfolio/        # Portfolio API
│   │   │   └── payments/         # Stripe integration
│   │   ├── services/
│   │   │   ├── ai_coach/         # OpenAI service
│   │   │   ├── signals_engine/   # Signal generation
│   │   │   ├── analytics/        # User analytics
│   │   │   └── notifications/    # Email/Telegram
│   │   ├── models/               # Database models
│   │   ├── core/                 # Core utilities
│   │   └── db/                   # Database config
│   ├── alembic/                  # DB migrations
│   ├── tests/
│   └── requirements.txt
├── docs/
├── docker-compose.yml
└── README.md
```

## Technical Constraints

### Performance Requirements
- **Page load time**: <2 seconds для критических страниц
- **API response time**: <500ms для user-facing endpoints  
- **AI response time**: <3 seconds для AI Coach responses
- **Uptime**: 99.9% availability target
- **Concurrent users**: Support для 1000+ simultaneous users

### Scalability Constraints
- **User base**: Готовность к 100K+ registered users
- **Content volume**: 1000+ lessons, videos, quizzes
- **Signal frequency**: 100+ signals per day
- **Storage**: 10TB+ для user-generated content
- **Bandwidth**: CDN для global content delivery

### Security Requirements
- **Data encryption**: AES-256 для sensitive data
- **API security**: Rate limiting, input validation, CORS
- **Payment security**: PCI DSS compliance через Stripe
- **User privacy**: GDPR compliance, data minimization
- **Content protection**: DRM для premium content

### Mobile Compatibility
- **Responsive design**: Mobile-first approach
- **PWA features**: Offline capabilities, push notifications
- **Performance**: <1MB initial bundle size
- **Touch interfaces**: Optimized для mobile interactions

## Dependencies Management

### Frontend Dependencies
```json
{
  "react": "^18.2.0",
  "typescript": "^5.0.0",
  "tailwindcss": "^3.3.0",
  "react-router-dom": "^6.8.0",
  "@tanstack/react-query": "^4.28.0",
  "react-hook-form": "^7.43.0",
  "framer-motion": "^10.0.0",
  "lucide-react": "^0.220.0",
  "lightweight-charts": "^4.0.0",
  "axios": "^1.3.0"
}
```

### Backend Dependencies
```txt
# Core Framework
fastapi==0.95.0
uvicorn==0.21.0
pydantic==2.0.0
sqlalchemy==2.0.0
alembic==1.10.0

# AI & ML
openai==0.27.0
langchain==0.0.150
pinecone-client==2.2.0
sentence-transformers==2.2.2
scikit-learn==1.2.2

# Authentication & Security
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.0.1
python-multipart==0.0.6

# Payments & Communications
stripe==5.4.0
python-telegram-bot==20.2
sendgrid==6.10.0

# Database & Caching
psycopg2-binary==2.9.6
redis==4.5.4
celery==5.2.7

# Monitoring
sentry-sdk==1.21.0
structlog==23.1.0
```

## Deployment Architecture

### Development Environment
- **Local setup**: Docker Compose для all services
- **Hot reload**: Frontend (Vite) + Backend (uvicorn --reload)
- **Database**: Local PostgreSQL + Redis containers
- **External APIs**: Development keys для AI services

### Staging Environment  
- **Infrastructure**: Vercel (Frontend) + Railway (Backend)
- **Database**: Managed PostgreSQL + Redis
- **Domain**: staging.tradingacademy.ai
- **CI/CD**: Automated deployment из main branch

### Production Environment
- **Frontend**: Vercel Pro с custom domain
- **Backend**: Railway Pro или AWS ECS
- **Database**: AWS RDS PostgreSQL + ElastiCache Redis
- **CDN**: Cloudflare для static assets
- **Monitoring**: Comprehensive logging и metrics
- **Backup**: Automated daily backups

### Scaling Strategy
- **Horizontal scaling**: Load balancers + multiple backend instances
- **Database scaling**: Read replicas для heavy queries
- **Caching**: Redis для session + content caching
- **CDN**: Global content distribution
- **AI services**: Rate limiting + fallback strategies

## AI Integration Architecture

### OpenAI Integration
- **GPT-4 API**: AI Coach conversations
- **Embeddings API**: Content similarity и personalization
- **Completion API**: Educational content generation
- **Moderation API**: User content filtering

### Custom AI Services
- **Signal Generation**: Technical analysis + news sentiment
- **Learning Path Optimization**: Adaptive difficulty adjustment
- **Content Recommendation**: Personalized lesson suggestions
- **Performance Analytics**: Trading performance insights

### Data Pipeline
```
User Interaction → Event Tracking → AI Analysis → Personalization → Content Delivery
       ↓                ↓              ↓               ↓               ↓
   Click/Read → Analytics DB → ML Processing → User Profile → Recommended Content
```

## Security Implementation

### Authentication Flow
```
Registration → Email Verification → Profile Setup → Dashboard Access
     ↓              ↓                   ↓              ↓
  JWT Token → Refresh Token → Session → API Access
```

### Payment Security
```
Stripe Checkout → Webhook → Account Upgrade → Feature Access
       ↓             ↓           ↓              ↓
   Secure Payment → Verification → Database → UI Update
```

### API Security
- **Rate limiting**: 100 requests/minute per user
- **Input validation**: Pydantic schemas для all endpoints
- **CORS policy**: Restricted to allowed origins
- **API versioning**: /api/v1/ namespace для stability
