# AI-Augmented Observability System for ISP

> **Final-Year Capstone Project** — Computer Networks & AI/ML  
> Complete end-to-end network observability platform combining real-time telemetry, machine learning anomaly detection, QoE estimation, and intelligent dashboards.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Problem Statement](#problem-statement)
3. [Proposed Solution](#proposed-solution)
4. [Key Features](#key-features)
5. [Technology Stack](#technology-stack)
6. [System Architecture](#system-architecture)
7. [Directory Structure](#directory-structure)
8. [Installation Prerequisites](#installation-prerequisites)
9. [Quick Start](#quick-start)
10. [Service URLs](#service-urls)
11. [Network Scenarios](#network-scenarios)
12. [API Reference](#api-reference)
13. [ML Methodology](#ml-methodology)
14. [Demonstration Workflow](#demonstration-workflow)
15. [Troubleshooting](#troubleshooting)
16. [Limitations](#limitations)
17. [Future Enhancements](#future-enhancements)

---

## Project Overview

The **AI-Augmented Observability System for ISP** is an integrated platform that continuously monitors simulated ISP network infrastructure, detects anomalous behavior using Machine Learning, estimates customer Quality of Experience (QoE), and exposes intelligent insights through REST APIs and interactive dashboards.

---

## Problem Statement

Internet Service Providers manage large network infrastructures generating continuous telemetry. Traditional monitoring systems display metrics in isolation, making it difficult to:

- Detect abnormal network behavior early
- Correlate multiple performance indicators
- Estimate customer Quality of Experience
- Distinguish normal variation from genuine degradation

This leads to delayed fault identification, poor network performance, and customer dissatisfaction.

---

## Proposed Solution

An AI-augmented system that:

1. **Collects** network telemetry via a realistic ISP network simulator
2. **Monitors** metrics through Prometheus time-series storage
3. **Records** recent network events alongside AI predictions in a bounded in-memory history
4. **Detects anomalies** using Isolation Forest (unsupervised ML)
5. **Classifies QoE** using Random Forest (supervised ML)
6. **Generates insights** through an AI decision engine
7. **Exposes data** via FastAPI REST endpoints
8. **Visualises** metrics in Grafana and network insights in a custom React dashboard

---

## Key Features

| Feature | Description |
|---------|-------------|
| 🔴 Live Network Simulation | 6 configurable ISP network scenarios with realistic noise |
| 📊 Prometheus Metrics | 10+ ISP-specific gauges/counters scraped every 10s |
| 📝 Network Events | Recent structured events derived from AI predictions |
| 🤖 Anomaly Detection | Isolation Forest on 8 network features |
| 📈 QoE Classification | Random Forest: GOOD / MODERATE / POOR |
| 🧠 AI Decision Engine | Combines all signals into health score + recommendations |
| 🌐 REST API | 15+ FastAPI endpoints with Swagger documentation |
| 📉 Grafana Dashboard | 13-panel dashboard auto-provisioned from JSON |
| ⚛️ React Frontend | NOC-style dark dashboard with live charts |
| 🐳 Docker Compose | Single command to start the complete stack |

---

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Simulator | Python + FastAPI | 3.10.x / 0.111 |
| ML Models | scikit-learn | 1.4.2 |
| Data | pandas + NumPy | 2.2.2 / 1.26.4 |
| API | FastAPI + uvicorn | 0.111 / 0.29 |
| Metrics | Prometheus | v2.51.2 |
| Dashboards | Grafana | 10.4.2 |
| Frontend | React + Vite | 18.3 / 8.3 |
| Charting | Recharts | 2.12.7 |
| Containers | Docker Compose | v3.8 |
| Static hosting | Cloudflare Pages | — |

---

## System Architecture

```
ISP NETWORK SIMULATOR (port 8001)
         │
    │
 /metrics
    │
Prometheus (port 9090)
    │
Grafana (port 3000)
    │
FastAPI / AI Service (port 8000) ← /telemetry
  ├── ML Inference (Isolation Forest + Random Forest)
  ├── AI Decision Engine
  ├── Bounded prediction/event history
  ├── /metrics (AI metrics for Prometheus)
  └── REST API endpoints
         │
React Frontend (port 5173 locally; Cloudflare Pages in production)
```

---

## Directory Structure

```
AI-AUGMENTED-OBSERVABILITY-ISP/
├── docker-compose.yml          # Orchestrates all services
├── .env.example                # Environment variable template
├── simulator/                  # ISP Network Simulator (FastAPI)
│   ├── app/
│   │   ├── main.py             # FastAPI app + background loop
│   │   ├── simulator.py        # Telemetry generator with noise
│   │   ├── scenarios.py        # 6 network scenario definitions
│   │   ├── metrics.py          # Prometheus metric definitions
│   │   └── config.py
├── api/                        # FastAPI ML + API service
│   ├── app/
│   │   ├── main.py             # FastAPI app + inference loop
│   │   ├── ml/
│   │   │   ├── train.py        # Dataset generation + model training
│   │   │   ├── inference.py    # Model loading + prediction
│   │   │   └── decision_engine.py  # AI health analysis
│   │   ├── ai_metrics.py       # AI → Prometheus metrics
│   │   ├── state.py            # Shared inference state
│   │   └── config.py
├── prometheus/
│   ├── prometheus.yml          # Scrape configuration
│   └── alerts/network_alerts.yml  # Alert rules
├── grafana/
│   ├── provisioning/           # Auto-provisioned datasource + dashboard
│   └── dashboards/isp_network_dashboard.json
├── frontend/                   # React + Vite dashboard and Cloudflare Pages config
│   └── src/
│       ├── pages/              # Dashboard, Anomaly, QoE, Events, Scenarios
│       ├── components/         # Reusable UI components
│       ├── hooks/              # usePoll polling hook
│       └── services/api.js     # API client
├── tests/
│   ├── unit/                   # Pytest unit tests
│   └── integration/            # Pytest integration tests
├── scripts/                    # PowerShell helper scripts
└── docs/                       # Technical documentation
```

---

## Installation Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Windows 11 | Any | Development environment |
| Docker Desktop | 4.x+ | With WSL2 backend enabled |
| Git | Any | For cloning |
| PowerShell | 5.1+ | For scripts |
| (Optional) Python | 3.10.8 | For running tests locally |

### Enable WSL2 for Docker Desktop

```powershell
# Enable WSL2 (run in PowerShell as Administrator)
wsl --install
# Restart your machine after installation
```

---

## Quick Start

```powershell
# 1. Clone or navigate to the project directory
cd D:\AI-AUGMENTED-OBSERVABILITY-ISP

# 2. Run setup (one-time)
.\scripts\setup.ps1

# 3. Change GRAFANA_ADMIN_PASSWORD in .env to a unique password before deployment

# 4. Start all services, build the frontend, and wait for health checks
.\scripts\start.ps1

# 5. Check all service health endpoints at any time
.\scripts\status.ps1
```

### ⚡ Single command to start everything:

```powershell
.\scripts\start.ps1
```

---

## Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| 🖥️ React Frontend | http://localhost:5173 | — |
| 🔌 FastAPI Backend | http://localhost:8000 | — |
| 📖 API Swagger Docs | http://localhost:8000/docs | — |
| 📡 Prometheus | http://localhost:9090 | — |
| 📊 Grafana | http://localhost:3000 | admin / value of `GRAFANA_ADMIN_PASSWORD` in `.env` |
| 🔧 Simulator | http://localhost:8001 | — |

### Cloudflare Pages + Render deployment

The React frontend is deployed at **https://isp-ai-observability.pages.dev/** and configured for Cloudflare Pages (`frontend/wrangler.jsonc`) with SPA route fallback. The root-level [`render.yaml`](./render.yaml) can deploy the FastAPI/ML API as a public Render web service and the simulator as a private service; the API talks to the simulator over Render's private network. Until the API is deployed and `VITE_API_URL` is set in Pages, the static frontend is live but data, scenario, and event APIs are unavailable.

1. Push this project to a Git provider supported by both Render and Cloudflare.
2. In Cloudflare Pages, create a Git-connected project named `isp-ai-observability`:
   - **Root directory:** `frontend`
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
   - Leave `VITE_API_URL` unset for the first build. After Render is deployed, set it to the API's HTTPS URL and redeploy.
3. In Render, create a Blueprint from the repository and use `render.yaml`. When prompted for `CORS_ORIGINS`, enter the Pages origin exactly, for example `https://isp-ai-observability.pages.dev` (no trailing slash).
4. Wait for the Render API health check to pass, then set the Pages `VITE_API_URL` build variable to the Render API HTTPS URL and trigger a new Pages deployment.
5. Verify the API at `<Render API URL>/health` and the dashboard at the Pages URL.

The Render Blueprint uses paid `starter` container plans; check Render's current pricing before creating resources. The simulator is private, but the API web service is publicly reachable and this prototype has no user authentication. Use only non-sensitive demo data; do not treat it as a production service until authentication and rate limiting are added. Prometheus and Grafana remain local Compose services and are not deployed by this Blueprint.

For a manual Pages deployment after authenticating Wrangler with Cloudflare, build first and deploy from the frontend directory:

```powershell
cd frontend
npm ci
npm run build
npx wrangler pages deploy dist --project-name isp-ai-observability
```

Live deployment requires a Git remote connected to both providers and authenticated Cloudflare/Render accounts. No provider credentials are stored in this repository.

---

## Network Scenarios

| Scenario | API Call | Key Characteristics |
|----------|----------|---------------------|
| Normal | `POST /scenario/normal` | Latency ~20ms, Loss ~0.1%, BW ~45% |
| High Latency | `POST /scenario/high-latency` | Latency ~180ms, Jitter ~40ms |
| Packet Loss | `POST /scenario/packet-loss` | Loss ~7.5%, Throughput ~45 Mbps |
| Congestion | `POST /scenario/congestion` | BW ~95%, Throughput ~30 Mbps |
| Router Overload | `POST /scenario/router-overload` | CPU ~92%, Memory ~87% |
| Recovery | `POST /scenario/recovery` | Metrics returning to normal |

**Via PowerShell:**
```powershell
# Activate high latency scenario
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/scenario/high-latency"
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/metrics` | GET | Prometheus metrics (AI outputs) |
| `/network-summary` | GET | Telemetry + full AI analysis |
| `/network-health` | GET | Health score + severity + recommendations |
| `/anomalies` | GET | Recent anomaly detection results |
| `/qoe` | GET | Current QoE classification |
| `/predictions` | GET | Rolling prediction history |
| `/events` | GET | Recent events derived from the bounded AI prediction history |
| `/model-info` | GET | ML model metadata + evaluation |
| `/predict/anomaly` | POST | On-demand anomaly detection |
| `/predict/qoe` | POST | On-demand QoE classification |
| `/scenario/{name}` | POST | Activate a simulation scenario |
| `/scenarios` | GET | List all available scenarios |

Full interactive documentation: **http://localhost:8000/docs**

---

## ML Methodology

### Model 1: Isolation Forest (Anomaly Detection)

- **Algorithm:** `sklearn.ensemble.IsolationForest`
- **Type:** Unsupervised anomaly detection
- **Features:** latency_ms, packet_loss_percent, jitter_ms, throughput_mbps, bandwidth_utilization_percent, router_cpu_percent, router_memory_percent, network_stress
- **Contamination:** 10% (expected anomaly fraction)
- **Training data:** 2,400 synthetic samples from 6 scenarios

### Model 2: Random Forest Classifier (QoE)

- **Algorithm:** `sklearn.ensemble.RandomForestClassifier`
- **Type:** Supervised multi-class classification
- **Classes:** GOOD (2), MODERATE (1), POOR (0)
- **Label methodology (synthetic):**
  - GOOD: latency < 60ms AND packet_loss < 1% AND bandwidth_util < 75%
  - POOR: latency > 130ms OR packet_loss > 5% OR bandwidth_util > 90%
  - MODERATE: all other observations

> ⚠️ **Important:** QoE labels are synthetic and rule-based. The classifier learns to generalise these rules — it does NOT measure actual customer satisfaction.

---

## Demonstration Workflow

```powershell
# Run the complete automated demo
.\scripts\demo.ps1
```

**Manual step-by-step:**

1. **Start:** `docker compose up --build -d`
2. **Open:** http://localhost:5173 (Dashboard), http://localhost:3000 (Grafana)
3. **Normal:** Observe healthy metrics
4. **High Latency:** `POST /scenario/high-latency` → Watch latency rise in Grafana
5. **Packet Loss:** `POST /scenario/packet-loss` → Watch anomaly detection trigger
6. **Congestion:** `POST /scenario/congestion` → Observe QoE change to POOR
7. **Router Overload:** `POST /scenario/router-overload` → CPU/Memory charts spike
8. **Recovery:** `POST /scenario/recovery` → Watch metrics normalize

---

## Troubleshooting

### Services not healthy after 5 minutes

```powershell
# Check logs for specific service
docker compose logs api
docker compose logs simulator
```

### ML models not loading

The API service trains models on first startup. If models fail:
```powershell
# Force retrain
docker compose exec api python -m app.ml.train
```

### Port conflicts

Check for conflicting processes:
```powershell
netstat -ano | findstr "9200\|9090\|3000\|8000\|5601"
```

---

## Limitations

1. **Synthetic telemetry** — All network metrics are simulated, not from real ISP infrastructure
2. **Synthetic QoE labels** — Labels are rule-based, not actual customer satisfaction surveys
3. **Local deployment only** — Not configured for production ISP environments
4. **No automatic remediation** — The system identifies issues but cannot fix them
5. **In-memory event history** — Recent event records are limited to the last 100 predictions and reset on API restart
6. **No authentication** — Development-mode security settings only; do not expose services publicly without an authenticated gateway

See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) for full details.

---

## Future Enhancements

- Real router telemetry via SNMP/gNMI
- NetFlow/sFlow traffic analysis
- Time-series forecasting (Prophet/LSTM)
- Multi-router topology monitoring
- Automated alert notifications (PagerDuty, email)
- Role-based access control
- Managed hosting for the Python API and simulator
- Real ISP customer satisfaction datasets
