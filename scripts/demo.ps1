# ============================================================
#  demo.ps1 - Complete end-to-end demonstration workflow
# ============================================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  ISP AI Observability - Demo Workflow" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$API = "http://localhost:8000"

function Invoke-Scenario {
    param([string]$Name, [string]$Display)
    Write-Host ""
    Write-Host ">>> Activating: $Display" -ForegroundColor Yellow
    try {
        $resp = Invoke-RestMethod -Method POST -Uri "$API/scenario/$Name" -TimeoutSec 5
        Write-Host "    Status: $($resp.status) - $($resp.description)" -ForegroundColor Green
        Start-Sleep -Seconds 15
        $health = Invoke-RestMethod -Uri "$API/network-health" -TimeoutSec 5
        Write-Host "    Health Score : $($health.health_score)" -ForegroundColor White
        Write-Host "    Severity     : $($health.severity)" -ForegroundColor White
        $qoe = Invoke-RestMethod -Uri "$API/qoe" -TimeoutSec 5
        Write-Host "    QoE Class    : $($qoe.qoe_class)" -ForegroundColor White
    } catch {
        Write-Host "    [WARN] Could not activate scenario: $_" -ForegroundColor Red
    }
}

Write-Host "Starting demo - ensure services are running (.\scripts\start.ps1)" -ForegroundColor Cyan
Write-Host "Open these URLs while the demo runs:" -ForegroundColor Cyan
Write-Host "  Grafana:  http://localhost:3000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host ""

Invoke-Scenario -Name "normal"         -Display "Normal Network Operation"
Invoke-Scenario -Name "high-latency"   -Display "High Latency Scenario"
Invoke-Scenario -Name "packet-loss"    -Display "Packet Loss Scenario"
Invoke-Scenario -Name "congestion"     -Display "Bandwidth Congestion"
Invoke-Scenario -Name "router-overload"-Display "Router Overload"
Invoke-Scenario -Name "recovery"       -Display "Network Recovery"

Write-Host ""
Write-Host "=== Demo complete ===" -ForegroundColor Cyan
Write-Host "Restoring normal scenario..." -ForegroundColor Yellow
Invoke-RestMethod -Method POST -Uri "$API/scenario/normal" | Out-Null
Write-Host "Done." -ForegroundColor Green
