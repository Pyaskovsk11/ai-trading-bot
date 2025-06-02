# Docker Desktop Factory Reset Script
Write-Host "🔄 Docker Desktop Factory Reset" -ForegroundColor Yellow

# Stop Docker Desktop completely
Write-Host "Stopping Docker Desktop..." -ForegroundColor Cyan
Get-Process "*docker*" | Stop-Process -Force -ErrorAction SilentlyContinue

# Wait for processes to stop
Start-Sleep 5

# Clear Docker data (be careful - this removes all containers/images)
$dockerData = "$env:APPDATA\Docker"
$dockerProgramData = "$env:PROGRAMDATA\Docker"

Write-Host "Clearing Docker data..." -ForegroundColor Yellow
if (Test-Path $dockerData) {
    Remove-Item $dockerData -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Cleared user Docker data" -ForegroundColor Green
}

if (Test-Path $dockerProgramData) {
    Remove-Item $dockerProgramData -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Cleared system Docker data" -ForegroundColor Green
}

# Restart Docker Desktop
Write-Host "Starting Docker Desktop..." -ForegroundColor Cyan
try {
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Write-Host "✅ Docker Desktop started" -ForegroundColor Green
    
    Write-Host "⏳ Please wait 2-3 minutes for Docker to initialize..." -ForegroundColor Yellow
    Write-Host "Then test with: docker version" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed to start Docker Desktop" -ForegroundColor Red
    Write-Host "Please start Docker Desktop manually from Start Menu" -ForegroundColor Yellow
}

Write-Host "`n🔧 If this doesn't work, try:" -ForegroundColor Blue
Write-Host "1. Uninstall Docker Desktop completely" -ForegroundColor Gray
Write-Host "2. Restart Windows" -ForegroundColor Gray  
Write-Host "3. Download fresh Docker Desktop from docker.com" -ForegroundColor Gray
Write-Host "4. Install as Administrator" -ForegroundColor Gray 