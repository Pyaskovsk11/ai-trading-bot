# Check Docker status
Write-Host "Checking Docker status..."
docker info
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Docker is not running. Please start Docker Desktop first."
    exit 1
}

# Stop existing containers
Write-Host "Stopping existing containers..."
docker-compose down

# Start PostgreSQL
Write-Host "Starting PostgreSQL..."
docker-compose up -d db

# Wait for database to be ready
Write-Host "Waiting for database to be ready..."
$maxAttempts = 30
$attempt = 0
$ready = $false

while (-not $ready -and $attempt -lt $maxAttempts) {
    $attempt++
    Write-Host "Attempt $attempt of $maxAttempts..."
    
    $result = docker exec ai_trading_bot-db-1 pg_isready -U postgres
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        Write-Host "Database is ready!"
    } else {
        Write-Host "Database is not ready yet. Waiting..."
        Start-Sleep -Seconds 2
    }
}

if (-not $ready) {
    Write-Host "Error: Database failed to start. Please check container logs."
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
.\.venv\Scripts\Activate.ps1

# Set environment variables
$env:PYTHONPATH = "$PWD\backend"

# Initialize database
Write-Host "Initializing database..."
python backend/app/db/init_db.py

# Start demo trading bot
Write-Host "Starting demo trading bot..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\Activate.ps1; `$env:PYTHONPATH = '$PWD\backend'; python backend/app/services/demo_trading_bot.py"

# Start FastAPI backend
Write-Host "Starting FastAPI backend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\Activate.ps1; `$env:PYTHONPATH = '$PWD\backend'; uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"

# Wait for backend to start
Write-Host "Waiting for backend to start..."
Start-Sleep -Seconds 10

# Start React frontend
Write-Host "Starting React frontend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm start"

# Start additional frontends
Write-Host "Starting trading bot UI..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\trading_bot_ui'; npm start"

Write-Host "Starting beszel dashboard..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\beszel\beszel\site'; npm run dev"

Write-Host "Application started successfully!"
Write-Host "API documentation: http://localhost:8000/docs"
Write-Host "Web interface: http://localhost:3000"
Write-Host "Trading bot UI: http://localhost:3001"
Write-Host "Beszel dashboard: http://localhost:4321"
Write-Host "Backend API: http://localhost:8000/api/v1" 