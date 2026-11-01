"""
simulator/app/main.py
FastAPI entry-point for the ISP Network Simulator.

Responsibilities:
  - Expose /metrics for Prometheus scraping.
  - Expose /health for Docker health checks.
  - Expose /scenario/* endpoints to switch simulation modes.
  - Run a background task that periodically generates telemetry and
    updates the Prometheus metrics.
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    generate_latest,
    REGISTRY,
)
from starlette.responses import Response

from .config import settings
from .logging_config import configure_logging
from .metrics import update_all_metrics
from .simulator import simulator
from .scenarios import SCENARIOS

configure_logging()
logger = logging.getLogger(__name__)


# ── Background telemetry loop ─────────────────────────────────────────────────

async def telemetry_loop() -> None:
    """
    Background coroutine that runs the simulation tick every
    `settings.simulator_interval` seconds.
    """
    logger.info(
        "Telemetry loop started (interval=%.1fs, scenario=%s)",
        settings.simulator_interval,
        simulator.current_scenario_name,
    )
    while True:
        try:
            telemetry = simulator.generate_telemetry()
            update_all_metrics(telemetry)
            logger.debug("Telemetry tick: scenario=%s latency=%.1fms",
                         telemetry["scenario"], telemetry["latency_ms"])
        except Exception as exc:
            logger.exception("Error in telemetry loop: %s", exc)
        await asyncio.sleep(settings.simulator_interval)


# ── Application lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background tasks on startup; clean up on shutdown."""
    task = asyncio.create_task(telemetry_loop())
    logger.info("ISP Network Simulator started on port %d", settings.simulator_port)
    yield
    task.cancel()
    logger.info("ISP Network Simulator stopped")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="ISP Network Simulator",
    description="Simulates ISP network telemetry and events for the AI Observability System.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Status"])
async def health() -> Dict[str, Any]:
    """Health check endpoint for Docker and load balancers."""
    return {
        "status": "healthy",
        "service": "isp-simulator",
        "scenario": simulator.current_scenario_name,
        "uptime_seconds": simulator.last_telemetry.get("uptime_seconds", 0)
        if simulator.last_telemetry else 0,
    }


@app.get("/metrics", tags=["Prometheus"])
async def prometheus_metrics() -> Response:
    """Expose all registered Prometheus metrics in text exposition format."""
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/telemetry", tags=["Simulator"])
async def get_telemetry() -> Dict[str, Any]:
    """Return the latest telemetry snapshot."""
    if simulator.last_telemetry is None:
        raise HTTPException(status_code=503, detail="Telemetry not yet available.")
    return simulator.last_telemetry


@app.get("/scenarios", tags=["Scenarios"])
async def list_scenarios() -> Dict[str, Any]:
    """List all available simulation scenarios."""
    return {
        "current": simulator.current_scenario_name,
        "available": [
            {
                "name": sc.name,
                "display_name": sc.display_name,
                "description": sc.description,
            }
            for sc in SCENARIOS.values()
        ],
    }


def _activate_scenario(scenario_name: str) -> Dict[str, Any]:
    """Helper: activate a scenario and return confirmation."""
    try:
        sc = simulator.set_scenario(scenario_name)
        logger.info("Scenario changed to: %s", scenario_name)
        return {
            "status": "activated",
            "scenario": sc.name,
            "display_name": sc.display_name,
            "description": sc.description,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/scenario/normal", tags=["Scenarios"])
async def scenario_normal() -> Dict[str, Any]:
    return _activate_scenario("normal")


@app.post("/scenario/high-latency", tags=["Scenarios"])
async def scenario_high_latency() -> Dict[str, Any]:
    return _activate_scenario("high-latency")


@app.post("/scenario/packet-loss", tags=["Scenarios"])
async def scenario_packet_loss() -> Dict[str, Any]:
    return _activate_scenario("packet-loss")


@app.post("/scenario/congestion", tags=["Scenarios"])
async def scenario_congestion() -> Dict[str, Any]:
    return _activate_scenario("congestion")


@app.post("/scenario/router-overload", tags=["Scenarios"])
async def scenario_router_overload() -> Dict[str, Any]:
    return _activate_scenario("router-overload")


@app.post("/scenario/recovery", tags=["Scenarios"])
async def scenario_recovery() -> Dict[str, Any]:
    return _activate_scenario("recovery")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.simulator_port,
        log_level="info",
    )
