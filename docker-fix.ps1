# Docker Desktop Fix Script
Write-Host "Docker Desktop Troubleshooting" -ForegroundColor Yellow

# Check if Docker Desktop is running
$dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
if ($dockerProcess) {
    Write-Host "Docker Desktop is running" -ForegroundColor Green
} else {
    Write-Host "Docker Desktop is NOT running" -ForegroundColor Red
}

# Test Docker command
Write-Host "Testing Docker..." -ForegroundColor Cyan
try {
    docker version >$null 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker is working!" -ForegroundColor Green
        exit 0
    }
} catch {}

Write-Host "Docker is not working. Attempting to fix..." -ForegroundColor Yellow

# Stop all Docker processes
$processes = @("Docker Desktop", "com.docker.backend", "com.docker.cli", "vpnkit")
foreach ($proc in $processes) {
    $p = Get-Process -Name $proc -ErrorAction SilentlyContinue
    if ($p) {
        Write-Host "Stopping $proc..." -ForegroundColor Yellow
        Stop-Process -Name $proc -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Waiting 5 seconds..." -ForegroundColor Cyan
Start-Sleep 5

# Start Docker Desktop
Write-Host "Starting Docker Desktop..." -ForegroundColor Cyan
try {
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Write-Host "Docker Desktop started. Waiting for initialization..." -ForegroundColor Green
    
    # Wait and test
    for ($i = 1; $i -le 6; $i++) {
        Write-Host "Waiting... ($i/6)" -ForegroundColor Cyan
        Start-Sleep 10
        
        docker version >$null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Docker is now working!" -ForegroundColor Green
            break
        }
    }
    
} catch {
    Write-Host "Failed to start Docker Desktop" -ForegroundColor Red
    Write-Host "Please start Docker Desktop manually" -ForegroundColor Yellow
}

Write-Host "Try these commands:" -ForegroundColor Yellow
Write-Host "docker context use desktop-linux" -ForegroundColor Gray
Write-Host "docker version" -ForegroundColor Gray 