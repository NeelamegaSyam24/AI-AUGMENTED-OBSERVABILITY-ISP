"""
api/app/main.py
FastAPI main application for the AI-Augmented ISP Observability System.

Responsibilities:
  - Load ML models on startup.
  - Run background polling loop: fetch telemetry → predict → store.
  - Expose all REST API endpoints.
  - Export AI metrics in Prometheus format.
  - Provide interactive Swagger/ReDoc documentation.
"""
import asyncio
import datetime
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from starlette.responses import Response

from .config import settings
from .state import engine, recent_predictions, latest_analysis, latest_telemetry
from .event_history import build_events
import app.state as _state
from .ai_metrics import update_ai_metrics
from .ml.decision_engine import analyze

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 10.0   # Fetch telemetry every 10 s


# ── Background polling loop ───────────────────────────────────────────────────

async def inference_loop() -> None:
    """
    Background task that:
      1. Fetches telemetry from the simulator.
      2. Runs anomaly detection + QoE classification.
      3. Generates AI analysis.
      4. Updates Prometheus AI metrics.
      5. Appends to rolling prediction history.
    """
    logger.info("Inference loop started (interval=%.0fs)", POLL_INTERVAL_SECONDS)
    async with httpx.AsyncClient(timeout=5.0) as client:
        while True:
            try:
                resp = await client.get(f"{settings.simulator_url}/telemetry")
                if resp.status_code == 200:
                    telemetry = resp.json()
                    _state.latest_telemetry = telemetry

                    if engine.is_loaded:
                        result = engine.predict_all(telemetry)
                        analysis = analyze(telemetry, result["anomaly"], result["qoe"])
                        _state.latest_analysis = analysis

                        update_ai_metrics(analysis)

                        prediction_record = {
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "scenario": telemetry.get("scenario", "unknown"),
                            "telemetry": telemetry,
                            "anomaly": result["anomaly"],
                            "qoe": result["qoe"],
                            "analysis": analysis,
                        }
                        _state.recent_predictions.append(prediction_record)
                        logger.debug(
                            "Prediction: scenario=%s anomaly=%s qoe=%s health=%.1f",
                            telemetry.get("scenario"),
                            result["anomaly"]["is_anomaly"],
                            result["qoe"]["qoe_class"],
                            analysis["health_score"],
                        )
            except httpx.ConnectError:
                logger.debug("Simulator not reachable yet — will retry")
            except Exception as exc:
                logger.warning("Inference loop error: %s", exc)

            await asyncio.sleep(POLL_INTERVAL_SECONDS)


# ── Application lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading ML models …")
    ok = engine.load()
    if not ok:
        logger.warning("Models failed to load — predictions will be unavailable")
    task = asyncio.create_task(inference_loop())
    logger.info("ISP AI API started on port %d", settings.api_port)
    yield
    task.cancel()
    logger.info("ISP AI API stopped")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI-Augmented ISP Observability API",
    description=(
        "REST API for the AI-Augmented Network Observability System for ISP. "
        "Provides anomaly detection, QoE classification, network health analysis, "
        "and scenario control."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper ────────────────────────────────────────────────────────────────────

def _require_analysis() -> Dict[str, Any]:
    if _state.latest_analysis is None:
        raise HTTPException(status_code=503, detail="No analysis data available yet. The system is still warming up.")
    return _state.latest_analysis


def _require_telemetry() -> Dict[str, Any]:
    if _state.latest_telemetry is None:
        raise HTTPException(status_code=503, detail="No telemetry data available yet.")
    return _state.latest_telemetry


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Status"])
async def health() -> Dict[str, Any]:
    """Health check endpoint. Returns current model load status."""
    return {
        "status": "healthy",
        "service": "isp-api",
        "models_loaded": engine.is_loaded,
        "has_telemetry": _state.latest_telemetry is not None,
        "predictions_count": len(_state.recent_predictions),
    }


@app.get("/metrics", tags=["Prometheus"])
async def prometheus_metrics() -> Response:
    """Expose AI-generated Prometheus metrics for scraping by Prometheus."""
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/network-summary", tags=["Network"])
async def network_summary() -> Dict[str, Any]:
    """Return a combined summary of current network telemetry and AI analysis."""
    telemetry = _require_telemetry()
    analysis  = _require_analysis()
    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "telemetry": telemetry,
        "analysis": analysis,
    }


@app.get("/network-health", tags=["Network"])
async def network_health() -> Dict[str, Any]:
    """Return the current network health score and severity."""
    analysis = _require_analysis()
    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "health_score": analysis["health_score"],
        "severity": analysis["severity"],
        "explanation": analysis["explanation"],
        "recommendations": analysis["recommendations"],
        "contributing_indicators": analysis["contributing_indicators"],
    }


@app.get("/anomalies", tags=["Anomaly Detection"])
async def get_anomalies(limit: int = Query(20, ge=1, le=100)) -> Dict[str, Any]:
    """Return the most recent anomaly detection results."""
    preds = list(_state.recent_predictions)
    anomaly_preds = [p for p in preds if p["anomaly"]["is_anomaly"]]
    return {
        "total_anomalies_in_window": len(anomaly_preds),
        "window_size": len(preds),
        "anomalies": anomaly_preds[-limit:][::-1],
    }


@app.get("/qoe", tags=["QoE"])
async def get_qoe() -> Dict[str, Any]:
    """Return the latest QoE classification result."""
    analysis = _require_analysis()
    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "qoe_class": analysis["qoe_class"],
        "qoe_score": analysis["qoe_score"],
        "class_probabilities": analysis["class_probabilities"],
    }


@app.get("/predictions", tags=["Predictions"])
async def get_predictions(limit: int = Query(20, ge=1, le=100)) -> Dict[str, Any]:
    """Return the most recent prediction records."""
    preds = list(_state.recent_predictions)[-limit:][::-1]
    return {
        "count": len(preds),
        "predictions": preds,
    }


@app.get("/events", tags=["Events"])
async def get_events(limit: int = Query(20, ge=1, le=100)) -> Dict[str, Any]:
    """
    Return recent network events derived from the bounded prediction history.
    """
    events = build_events(list(_state.recent_predictions), limit)
    return {"source": "prediction_history", "count": len(events), "events": events}


@app.post("/predict/anomaly", tags=["Predictions"])
async def predict_anomaly(telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run anomaly detection on a submitted telemetry payload.
    Accepts raw metric values and returns Isolation Forest output.
    """
    if not engine.is_loaded:
        raise HTTPException(status_code=503, detail="ML models not loaded.")
    result = engine.predict_anomaly(telemetry)
    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "input": telemetry,
        "result": result,
    }


@app.post("/predict/qoe", tags=["Predictions"])
async def predict_qoe(telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run QoE classification on a submitted telemetry payload.
    """
    if not engine.is_loaded:
        raise HTTPException(status_code=503, detail="ML models not loaded.")
    result = engine.predict_qoe(telemetry)
    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "input": telemetry,
        "result": result,
    }


@app.get("/model-info", tags=["ML"])
async def model_info() -> Dict[str, Any]:
    """Return ML model metadata including training parameters and evaluation metrics."""
    if not engine.is_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded.")
    return {
        "models_loaded": True,
        "metadata": engine.metadata,
    }


# ── Scenario proxy endpoints ──────────────────────────────────────────────────

async def _proxy_scenario(scenario_path: str) -> Dict[str, Any]:
    """Forward a scenario activation request to the simulator."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(f"{settings.simulator_url}/scenario/{scenario_path}")
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Simulator unreachable: {exc}")


@app.post("/scenario/normal", tags=["Scenarios"])
async def scenario_normal():
    return await _proxy_scenario("normal")

@app.post("/scenario/high-latency", tags=["Scenarios"])
async def scenario_high_latency():
    return await _proxy_scenario("high-latency")

@app.post("/scenario/packet-loss", tags=["Scenarios"])
async def scenario_packet_loss():
    return await _proxy_scenario("packet-loss")

@app.post("/scenario/congestion", tags=["Scenarios"])
async def scenario_congestion():
    return await _proxy_scenario("congestion")

@app.post("/scenario/router-overload", tags=["Scenarios"])
async def scenario_router_overload():
    return await _proxy_scenario("router-overload")

@app.post("/scenario/recovery", tags=["Scenarios"])
async def scenario_recovery():
    return await _proxy_scenario("recovery")

@app.get("/scenarios", tags=["Scenarios"])
async def list_scenarios():
    """List all available simulation scenarios."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.simulator_url}/scenarios")
            return resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level="info",
    )
