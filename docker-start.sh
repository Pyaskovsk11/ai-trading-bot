#!/bin/bash

# ===========================================
# 🐳 AI Trading Bot - Docker Launcher
# ===========================================

echo "🚀 Starting AI Trading Bot Docker Stack..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Проверка Docker
if ! command -v docker &> /dev/null; then
    error "Docker не установлен. Установите Docker Desktop для Windows"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    error "Docker Compose не найден"
    exit 1
fi

# Проверка файлов
log "Проверка необходимых файлов..."

if [ ! -f "docker-compose.yml" ]; then
    error "docker-compose.yml не найден"
    exit 1
fi

if [ ! -f "backend/Dockerfile" ]; then
    error "backend/Dockerfile не найден"
    exit 1
fi

# Создание директорий
log "Создание необходимых директорий..."
mkdir -p logs
mkdir -p database/init

# Остановка предыдущих контейнеров
log "Остановка предыдущих контейнеров..."
docker-compose down --remove-orphans 2>/dev/null || docker compose down --remove-orphans 2>/dev/null

# Очистка старых образов (опционально)
read -p "🗑️  Очистить старые Docker образы? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Очистка старых образов..."
    docker system prune -f
    docker volume prune -f
fi

# Сборка и запуск
log "Сборка и запуск контейнеров..."

# Используем docker compose или docker-compose в зависимости от версии
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

# Сборка с принудительным пересозданием
$DOCKER_COMPOSE_CMD build --no-cache --pull

# Запуск инфраструктуры сначала
log "Запуск инфраструктуры (PostgreSQL, Redis)..."
$DOCKER_COMPOSE_CMD up -d postgres redis

# Ожидание готовности БД
log "Ожидание готовности базы данных..."
sleep 10

# Проверка готовности PostgreSQL
log "Проверка готовности PostgreSQL..."
for i in {1..30}; do
    if docker exec trading_bot_postgres pg_isready -U trading_user -d trading_bot > /dev/null 2>&1; then
        log "✅ PostgreSQL готов"
        break
    fi
    echo -n "."
    sleep 2
done

# Проверка готовности Redis
log "Проверка готовности Redis..."
for i in {1..15}; do
    if docker exec trading_bot_redis redis-cli ping > /dev/null 2>&1; then
        log "✅ Redis готов"
        break
    fi
    echo -n "."
    sleep 2
done

# Запуск основных сервисов
log "Запуск backend..."
$DOCKER_COMPOSE_CMD up -d backend

# Ожидание готовности backend
log "Ожидание готовности backend API..."
sleep 15

# Проверка здоровья backend
for i in {1..20}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log "✅ Backend API готов"
        break
    fi
    echo -n "."
    sleep 3
done

# Запуск остальных сервисов
log "Запуск остальных сервисов..."
$DOCKER_COMPOSE_CMD up -d

# Финальная проверка
sleep 5
log "🔍 Проверка статуса контейнеров..."
$DOCKER_COMPOSE_CMD ps

echo
log "🎉 AI Trading Bot успешно запущен!"
echo
echo -e "${BLUE}📊 Доступные интерфейсы:${NC}"
echo -e "${GREEN}• Backend API:    http://localhost:8000${NC}"
echo -e "${GREEN}• Health Check:   http://localhost:8000/health${NC}"
echo -e "${GREEN}• API Docs:       http://localhost:8000/docs${NC}"
echo -e "${GREEN}• Trading UI:     http://localhost:8000/trading-control${NC}"
echo -e "${GREEN}• Frontend:       http://localhost:3000${NC}"
echo -e "${GREEN}• pgAdmin:        http://localhost:8080${NC}"
echo
echo -e "${BLUE}🔧 Полезные команды:${NC}"
echo -e "${YELLOW}• Просмотр логов:    docker-compose logs -f${NC}"
echo -e "${YELLOW}• Остановка:         docker-compose down${NC}"
echo -e "${YELLOW}• Перезапуск:        docker-compose restart${NC}"
echo
log "Для просмотра логов в реальном времени: docker-compose logs -f" 