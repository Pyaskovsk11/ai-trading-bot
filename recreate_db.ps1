# Переход в папку backend
Set-Location backend

# Активация виртуального окружения
.\\.venv\\Scripts\\Activate.ps1

# Возврат в корень проекта
Set-Location ..

# Функция для проверки статуса выполнения
function Test-CommandStatus {
    param (
        [string]$Command,
        [string]$ErrorMessage
    )
    if ($LASTEXITCODE -ne 0) {
        Write-Error "$ErrorMessage (Exit code: $LASTEXITCODE)"
        exit 1
    }
}

try {
    # Остановка всех контейнеров
    Write-Host "Stopping all containers..."
    docker-compose down
    Test-CommandStatus "docker-compose down" "Failed to stop containers"

    # Запуск PostgreSQL
    Write-Host "Starting PostgreSQL..."
    docker-compose up -d db
    Test-CommandStatus "docker-compose up -d db" "Failed to start PostgreSQL"

    # Ожидание готовности базы данных
    Write-Host "Waiting for database to be ready..."
    $maxAttempts = 30
    $attempt = 0
    $isReady = $false

    while (-not $isReady -and $attempt -lt $maxAttempts) {
        try {
            $result = docker-compose exec -T db pg_isready
            if ($LASTEXITCODE -eq 0) {
                $isReady = $true
                Write-Host "Database is ready!"
            }
        } catch {
            $attempt++
            Write-Host "Waiting for database... Attempt $attempt of $maxAttempts"
            Start-Sleep -Seconds 2
        }
    }

    if (-not $isReady) {
        throw "Database failed to become ready after $maxAttempts attempts"
    }

    # Пересоздание базы данных
    Write-Host "Recreating database..."
    python backend/app/db/init_db.py
    Test-CommandStatus "python backend/app/db/init_db.py" "Failed to recreate database"

    # Перезапуск приложения
    Write-Host "Restarting application..."
    docker-compose up -d
    Test-CommandStatus "docker-compose up -d" "Failed to restart application"

    Write-Host "Database recreated and application restarted successfully!" -ForegroundColor Green
} catch {
    Write-Error "An error occurred: $_"
    exit 1
}