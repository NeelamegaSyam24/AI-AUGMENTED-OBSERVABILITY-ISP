param(
    [switch]$Wait,
    [int]$TimeoutSeconds = 600
)

# ============================================================
#  status.ps1 - Check status of all running services
# ============================================================
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  ISP AI Observability - Service Status" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
docker compose ps

if ($LASTEXITCODE -ne 0) {
    throw "Unable to query Docker Compose service status."
}

$services = @(
    @{ Name = "Frontend";      Port = "FRONTEND_PORT";      DefaultPort = 5173; Path = "/" },
    @{ Name = "Simulator";     Port = "SIMULATOR_PORT";     DefaultPort = 8001; Path = "/health" },
    @{ Name = "FastAPI";       Port = "API_PORT";           DefaultPort = 8000; Path = "/health" },
    @{ Name = "Prometheus";    Port = "PROMETHEUS_PORT";    DefaultPort = 9090; Path = "/-/healthy" },
    @{ Name = "Grafana";       Port = "GRAFANA_PORT";       DefaultPort = 3000; Path = "/api/health" }
)

$settings = @{}
if (Test-Path ".env") {
    foreach ($line in Get-Content ".env") {
        if ($line -match '^\s*([^#=]+)=(.*)$') {
            $settings[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
}
$serviceHost = if ($settings.ContainsKey("HOST_IP")) { $settings["HOST_IP"] } else { "127.0.0.1" }
if ($serviceHost -eq "0.0.0.0") {
    $serviceHost = "localhost"
}
foreach ($svc in $services) {
    $port = if ($settings.ContainsKey($svc.Port)) { $settings[$svc.Port] } else { $svc.DefaultPort }
    $svc.Url = "http://${serviceHost}:${port}$($svc.Path)"
}

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
do {
    $failed = @()
    foreach ($svc in $services) {
        try {
            Invoke-WebRequest -Uri $svc.Url -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop | Out-Null
        } catch {
            $failed += $svc.Name
        }
    }

    if ($failed.Count -eq 0) {
        break
    }
    if (-not $Wait -or (Get-Date) -ge $deadline) {
        break
    }
    Write-Host "Waiting for: $($failed -join ', ')" -ForegroundColor Yellow
    Start-Sleep -Seconds 5
} while ($true)

Write-Host ""
Write-Host "Health checks:" -ForegroundColor Cyan
foreach ($svc in $services) {
    if ($failed -contains $svc.Name) {
        Write-Host "  [FAIL] $($svc.Name) is not reachable" -ForegroundColor Red
    } else {
        Write-Host "  [OK] $($svc.Name) is healthy" -ForegroundColor Green
    }
}
if ($failed.Count -gt 0) {
    throw "Service health checks failed: $($failed -join ', ')"
}
