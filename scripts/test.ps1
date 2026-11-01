# ============================================================
#  test.ps1 - Run all unit and integration tests
# ============================================================
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  ISP AI Observability - Running Tests" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Install test deps if needed
pip install -r tests\requirements.txt -q

Write-Host ""
Write-Host "Running unit tests..." -ForegroundColor Yellow
pytest tests\unit\ -v

Write-Host ""
Write-Host "Running integration tests (requires running services)..." -ForegroundColor Yellow
pytest tests\integration\ -v
