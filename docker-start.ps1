# ===========================================
# 🐳 AI Trading Bot - Docker Launcher (Windows)
# ===========================================

Write-Host "🚀 Starting AI Trading Bot Docker Stack..." -ForegroundColor Green

# Функции логирования
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] WARNING: $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] ERROR: $Message" -ForegroundColor Red
}

# Проверка Docker
try {
    docker --version | Out-Null
    Write-Log "✅ Docker найден"
} catch {
    Write-Error "Docker не установлен. Установите Docker Desktop для Windows"
    exit 1
}

# Проверка Docker Compose
try {
    docker compose version | Out-Null
    $dockerComposeCmd = "docker compose"
    Write-Log "✅ Docker Compose найден"
} catch {
    try {
        docker-compose --version | Out-Null
        $dockerComposeCmd = "docker-compose"
        Write-Log "✅ Docker Compose (legacy) найден"
    } catch {
        Write-Error "Docker Compose не найден"
        exit 1
    }
}

# Проверка файлов
Write-Log "Проверка необходимых файлов..."

if (!(Test-Path "docker-compose.yml")) {
    Write-Error "docker-compose.yml не найден"
    exit 1
}

if (!(Test-Path "backend/Dockerfile")) {
    Write-Error "backend/Dockerfile не найден"
    exit 1
}

# Создание директорий
Write-Log "Создание необходимых директорий..."
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "database/init" | Out-Null

# Остановка предыдущих контейнеров
Write-Log "Остановка предыдущих контейнеров..."
& $dockerComposeCmd down --remove-orphans 2>$null

# Очистка старых образов (опционально)
$choice = Read-Host "🗑️  Очистить старые Docker образы? (y/N)"
if ($choice -eq "y" -or $choice -eq "Y") {
    Write-Log "Очистка старых образов..."
    docker system prune -f
    docker volume prune -f
}

# Сборка и запуск
Write-Log "Сборка и запуск контейнеров..."

# Сборка с принудительным пересозданием
Write-Log "Сборка образов..."
& $dockerComposeCmd build --no-cache --pull

# Запуск инфраструктуры сначала
Write-Log "Запуск инфраструктуры (PostgreSQL, Redis)..."
& $dockerComposeCmd up -d postgres redis

# Ожидание готовности БД
Write-Log "Ожидание готовности базы данных..."
Start-Sleep 10

# Проверка готовности PostgreSQL
Write-Log "Проверка готовности PostgreSQL..."
for ($i = 1; $i -le 30; $i++) {
    try {
        docker exec trading_bot_postgres pg_isready -U trading_user -d trading_bot 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ PostgreSQL готов"
            break
        }
    } catch {}
    Write-Host "." -NoNewline
    Start-Sleep 2
}

# Проверка готовности Redis
Write-Log "`nПроверка готовности Redis..."
for ($i = 1; $i -le 15; $i++) {
    try {
        docker exec trading_bot_redis redis-cli ping 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Redis готов"
            break
        }
    } catch {}
    Write-Host "." -NoNewline
    Start-Sleep 2
}

# Запуск основных сервисов
Write-Log "`nЗапуск backend..."
& $dockerComposeCmd up -d backend

# Ожидание готовности backend
Write-Log "Ожидание готовности backend API..."
Start-Sleep 15

# Проверка здоровья backend
Write-Log "Проверка здоровья backend..."
for ($i = 1; $i -le 20; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Log "✅ Backend API готов"
            break
        }
    } catch {}
    Write-Host "." -NoNewline
    Start-Sleep 3
}

# Запуск остальных сервисов
Write-Log "`nЗапуск остальных сервисов..."
& $dockerComposeCmd up -d

# Финальная проверка
Start-Sleep 5
Write-Log "🔍 Проверка статуса контейнеров..."
& $dockerComposeCmd ps

Write-Host ""
Write-Log "🎉 AI Trading Bot успешно запущен!"
Write-Host ""
Write-Host "📊 Доступные интерфейсы:" -ForegroundColor Blue
Write-Host "• Backend API:    http://localhost:8000" -ForegroundColor Green
Write-Host "• Health Check:   http://localhost:8000/health" -ForegroundColor Green
Write-Host "• API Docs:       http://localhost:8000/docs" -ForegroundColor Green
Write-Host "• Trading UI:     http://localhost:8000/trading-control" -ForegroundColor Green
Write-Host "• Frontend:       http://localhost:3000" -ForegroundColor Green
Write-Host "• pgAdmin:        http://localhost:8080" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 Полезные команды:" -ForegroundColor Blue
Write-Host "• Просмотр логов:    $dockerComposeCmd logs -f" -ForegroundColor Yellow
Write-Host "• Остановка:         $dockerComposeCmd down" -ForegroundColor Yellow
Write-Host "• Перезапуск:        $dockerComposeCmd restart" -ForegroundColor Yellow
Write-Host ""
Write-Log "Для просмотра логов в реальном времени: $dockerComposeCmd logs -f" 