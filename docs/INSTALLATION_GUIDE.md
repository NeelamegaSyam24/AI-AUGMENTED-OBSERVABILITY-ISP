# Installation Guide — Windows 11 + Docker Desktop

## Prerequisites

### 1. Enable Windows Subsystem for Linux (WSL2)

Open PowerShell as Administrator:
```powershell
wsl --install
```
Restart your machine after installation.

### 2. Install Docker Desktop

1. Download from: https://www.docker.com/products/docker-desktop/
2. Run the installer
3. During setup, select "Use WSL2 instead of Hyper-V"
4. Start Docker Desktop and wait for it to show "Docker is running"

### 3. Verify Docker installation

```powershell
docker --version
docker compose version
```

Expected output:
```
Docker version 25.x.x
Docker Compose version v2.x.x
```

### 4. Configure Docker resources (recommended)

In Docker Desktop → Settings → Resources:
- **Memory**: 4 GB minimum
- **CPU**: 4 cores minimum
- **Disk**: 10 GB minimum

---

## Project Setup

### Step 1: Navigate to project directory

```powershell
cd D:\AI-AUGMENTED-OBSERVABILITY-ISP
```

### Step 2: Run setup script (one-time)

```powershell
.\scripts\setup.ps1
```

This creates the `.env` file and necessary directories.

### Step 3: Start all services

```powershell
docker compose up --build -d
```

**First run** will:
- Build all Docker images
- Pull the Python, Prometheus, and Grafana base images
- Train ML models (~30 seconds)
- Start all services

**Subsequent runs** (images already built):
```powershell
docker compose up -d
```

### Step 4: Verify all services are healthy

```powershell
.\scripts\status.ps1
```

Or check Docker Desktop's container list.

### Step 5: Wait for services to be ready

- **Prometheus**: Ready immediately
- **Grafana**: ~30 seconds
- **Simulator**: ~10 seconds
- **API**: ~30-60 seconds (after training ML models)
- **Frontend**: ~30 seconds

---

## Accessing the Application

Once all services are healthy:

| Service | URL |
|---------|-----|
| React Frontend | http://localhost:5173 |
| FastAPI Swagger | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin123) |
| Simulator API | http://localhost:8001/docs |

---

## Stopping the Application

```powershell
# Stop all containers (preserves data volumes)
docker compose down

# Stop and remove all data volumes (clean start)
docker compose down -v
```

---

## Troubleshooting

### Services not starting after `docker compose up`

```powershell
# View logs for a specific service
docker compose logs -f api
docker compose logs -f simulator
```

### Port conflicts

```powershell
# Find what's using a common service port
netstat -ano | findstr ":8000"
# Kill process by PID
Stop-Process -Id <PID> -Force
```

### Frontend shows "Cannot connect to API"

Ensure the API container is healthy:
```powershell
docker compose ps api
curl http://localhost:8000/health
```

### ML models not loading in API

```powershell
# Manually trigger model training
docker compose exec api python -m app.ml.train
docker compose restart api
```

### Complete reset

```powershell
docker compose down -v --remove-orphans
docker compose up --build -d
```

---

## Running Tests Locally (Optional)

If you have Python 3.10+ installed locally:

```powershell
# Install test dependencies
pip install -r tests\requirements.txt

# Run unit tests (no services required)
pytest tests\unit\ -v

# Run integration tests (requires running services)
pytest tests\integration\ -v
```
