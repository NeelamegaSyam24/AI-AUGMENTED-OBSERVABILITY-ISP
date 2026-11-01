# ============================================================
#  start.ps1 - Start all ISP AI Observability services
# ============================================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  ISP AI Observability - Starting Services" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

docker compose up --build -d
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker Compose failed to start the services."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Waiting for all services to become healthy..." -ForegroundColor Yellow
& "$PSScriptRoot\status.ps1" -Wait -TimeoutSeconds 600
if ($LASTEXITCODE -ne 0) {
    Write-Error "One or more services did not become healthy. Check: docker compose logs"
    exit 1
}

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

Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Cyan
foreach ($service in @(
    @{ Name = "Frontend"; Port = "FRONTEND_PORT"; DefaultPort = 5173 },
    @{ Name = "FastAPI"; Port = "API_PORT"; DefaultPort = 8000 },
    @{ Name = "API Docs"; Port = "API_PORT"; DefaultPort = 8000; Path = "/docs" },
    @{ Name = "Prometheus"; Port = "PROMETHEUS_PORT"; DefaultPort = 9090 },
    @{ Name = "Grafana"; Port = "GRAFANA_PORT"; DefaultPort = 3000 },
    @{ Name = "Simulator"; Port = "SIMULATOR_PORT"; DefaultPort = 8001 }
)) {
    $port = if ($settings.ContainsKey($service.Port)) { $settings[$service.Port] } else { $service.DefaultPort }
    $path = if ($service.ContainsKey("Path")) { $service.Path } else { "" }
    Write-Host ("  {0}: http://{1}:{2}{3}" -f $service.Name, $serviceHost, $port, $path) -ForegroundColor White
}
