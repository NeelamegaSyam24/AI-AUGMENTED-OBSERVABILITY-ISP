# ============================================================
#  setup.ps1 - One-time project setup for Windows 11
#  Run this script BEFORE the first docker compose up
# ============================================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  ISP AI Observability - Project Setup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Check Docker
try {
    docker info | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is unavailable."
    }
    Write-Host "[OK] Docker Desktop is running." -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker Desktop is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Copy .env if missing
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] Created .env from .env.example" -ForegroundColor Green
} else {
    Write-Host "[OK] .env already exists" -ForegroundColor Green
}

# Create model output directory
New-Item -ItemType Directory -Force -Path "api\app\models" | Out-Null
Write-Host "[OK] Created api/app/models directory" -ForegroundColor Green

Write-Host ""
Write-Host "Setup complete. Run .\scripts\start.ps1 to start the application." -ForegroundColor Cyan
