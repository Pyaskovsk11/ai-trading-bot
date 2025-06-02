# 🚀 AI Trading Bot - Автоматический запуск Backend
# Решает проблемы с портами и запускает сервер для бэктестинга

Write-Host "🤖 AI Trading Bot - Auto Startup" -ForegroundColor Cyan
Write-Host "🔧 Решение проблем с портами..." -ForegroundColor Yellow

# Остановка всех процессов Python
Write-Host "🔄 Остановка старых процессов..." -ForegroundColor Yellow
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Освобождение порта 8000
$processes = netstat -ano | Select-String ":8000.*LISTENING"
if ($processes) {
    foreach ($process in $processes) {
        $processId = ($process -split '\s+')[-1]
        Write-Host "🔄 Завершаю процесс PID $processId на порту 8000" -ForegroundColor Yellow
        taskkill /F /PID $processId 2>$null
    }
}

Start-Sleep -Seconds 2

# Переход в папку backend
Set-Location "backend"

Write-Host ""
Write-Host "🚀 ЗАПУСК AI TRADING BOT BACKEND" -ForegroundColor Green
Write-Host "📊 БЭКТЕСТИНГ И AI ТРЕНИРОВКА ГОТОВЫ!" -ForegroundColor Green
Write-Host "🌐 API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📖 Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🎯 Бэктест: http://localhost:8000/api/v1/test-backtest" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

# Запуск backend
try {
    python start_backend.py
} catch {
    Write-Host "⚠️  Fallback: запуск обычным способом" -ForegroundColor Yellow
    python working_main.py
} 