"""
api/app/ai_metrics.py
Prometheus metrics exported by the AI/ML service.

These metrics allow Grafana to visualize AI model outputs
alongside raw network telemetry scraped from the simulator.
"""
from prometheus_client import Gauge

# ── AI decision outputs ───────────────────────────────────────────────────────

isp_ai_anomaly_detected = Gauge(
    "isp_ai_anomaly_detected",
    "1 if the Isolation Forest model detected an anomaly, 0 otherwise",
)

isp_ai_anomaly_score = Gauge(
    "isp_ai_anomaly_score",
    "Isolation Forest anomaly score (more negative = more anomalous)",
)

isp_ai_qoe_score = Gauge(
    "isp_ai_qoe_score",
    "QoE classification score: 2=GOOD, 1=MODERATE, 0=POOR",
)

isp_ai_health_score = Gauge(
    "isp_ai_health_score",
    "Overall network health score (0-100), computed by the AI decision engine",
)

isp_ai_severity = Gauge(
    "isp_ai_severity",
    "Network severity level: 0=HEALTHY, 1=WARNING, 2=CRITICAL",
)


def update_ai_metrics(analysis: dict) -> None:
    """Update all AI-related Prometheus gauges from a decision analysis result."""
    isp_ai_anomaly_detected.set(1 if analysis.get("is_anomaly") else 0)
    isp_ai_anomaly_score.set(analysis.get("anomaly_score", 0.0))
    isp_ai_qoe_score.set(analysis.get("qoe_score", -1))
    isp_ai_health_score.set(analysis.get("health_score", 0.0))

    severity_map = {"HEALTHY": 0, "WARNING": 1, "CRITICAL": 2}
    isp_ai_severity.set(severity_map.get(analysis.get("severity", "HEALTHY"), 0))
