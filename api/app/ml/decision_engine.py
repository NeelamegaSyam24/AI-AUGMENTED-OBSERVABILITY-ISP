"""
api/app/ml/decision_engine.py
AI Decision and Insight Layer.

Combines network telemetry + Isolation Forest result + QoE classification
into a comprehensive, human-readable network health assessment.

Output includes:
  - Health score (0–100)
  - Severity level: HEALTHY / WARNING / CRITICAL
  - Anomaly status
  - QoE category
  - Contributing indicators
  - Human-readable explanation
  - Investigation recommendations

All thresholds are configurable via constants and are transparent/explainable.
Note: recommendations identify areas to investigate, NOT confirmed root causes.
"""
from typing import Dict, Any, List


# ── Threshold constants (all tunable) ────────────────────────────────────────

LATENCY_WARNING_MS     = 80.0
LATENCY_CRITICAL_MS    = 140.0

PACKET_LOSS_WARNING    = 2.0    # percent
PACKET_LOSS_CRITICAL   = 5.0   # percent

JITTER_WARNING_MS      = 20.0
JITTER_CRITICAL_MS     = 35.0

THROUGHPUT_WARNING     = 70.0   # Mbps (below = concern)
THROUGHPUT_CRITICAL    = 40.0   # Mbps

BW_UTIL_WARNING        = 80.0   # percent
BW_UTIL_CRITICAL       = 92.0  # percent

CPU_WARNING            = 80.0   # percent
CPU_CRITICAL           = 90.0  # percent

MEM_WARNING            = 78.0   # percent
MEM_CRITICAL           = 88.0  # percent

# Health score weight definitions (must sum to 1.0)
WEIGHTS = {
    "latency":    0.25,
    "packet_loss":0.25,
    "bandwidth":  0.20,
    "throughput": 0.15,
    "router_res": 0.15,
}


def _compute_metric_health(value: float, warn: float, crit: float,
                            inverse: bool = False) -> float:
    """
    Map a single metric to a 0–100 health sub-score.

    Args:
        inverse: If True, higher value = worse (e.g. latency, packet_loss).
                 If False, lower value = worse (e.g. throughput).
    """
    if not inverse:
        # Lower is worse (throughput)
        if value >= warn:
            return 100.0
        elif value >= crit:
            return 50.0
        else:
            return 0.0
    else:
        # Higher is worse (latency, packet loss, etc.)
        if value <= warn:
            return 100.0
        elif value <= crit:
            return 50.0
        else:
            return 0.0


def calculate_health_score(telemetry: Dict[str, Any]) -> float:
    """
    Compute a weighted network health score (0–100).

    Formula:
      score = sum(weight_i * metric_health_i)
    where metric_health_i ∈ {0, 50, 100} based on thresholds.
    """
    lat  = telemetry.get("latency_ms", 0.0)
    pl   = telemetry.get("packet_loss_percent", 0.0)
    jit  = telemetry.get("jitter_ms", 0.0)
    tp   = telemetry.get("throughput_mbps", 100.0)
    bw   = telemetry.get("bandwidth_utilization_percent", 0.0)
    cpu  = telemetry.get("router_cpu_percent", 0.0)
    mem  = telemetry.get("router_memory_percent", 0.0)

    lat_h  = _compute_metric_health(lat,  LATENCY_WARNING_MS,  LATENCY_CRITICAL_MS,  inverse=True)
    pl_h   = _compute_metric_health(pl,   PACKET_LOSS_WARNING, PACKET_LOSS_CRITICAL, inverse=True)
    bw_h   = _compute_metric_health(bw,   BW_UTIL_WARNING,     BW_UTIL_CRITICAL,     inverse=True)
    tp_h   = _compute_metric_health(tp,   THROUGHPUT_WARNING,  THROUGHPUT_CRITICAL,  inverse=False)
    cpu_h  = _compute_metric_health(cpu,  CPU_WARNING,         CPU_CRITICAL,         inverse=True)
    mem_h  = _compute_metric_health(mem,  MEM_WARNING,         MEM_CRITICAL,         inverse=True)
    res_h  = (cpu_h + mem_h) / 2.0

    score = (
        WEIGHTS["latency"]     * lat_h
        + WEIGHTS["packet_loss"] * pl_h
        + WEIGHTS["bandwidth"]   * bw_h
        + WEIGHTS["throughput"]  * tp_h
        + WEIGHTS["router_res"]  * res_h
    )
    return round(score, 2)


def get_severity(health_score: float, is_anomaly: bool, qoe_class: str) -> str:
    """
    Determine overall severity level from health score, anomaly, and QoE.

    CRITICAL: health < 40 OR (is_anomaly AND qoe == POOR)
    WARNING:  health < 70 OR is_anomaly OR qoe == MODERATE
    HEALTHY:  otherwise
    """
    if health_score < 40 or (is_anomaly and qoe_class == "POOR"):
        return "CRITICAL"
    elif health_score < 70 or is_anomaly or qoe_class in ("MODERATE", "POOR"):
        return "WARNING"
    else:
        return "HEALTHY"


def identify_contributing_indicators(telemetry: Dict[str, Any]) -> List[str]:
    """Return a list of metric names that are outside acceptable ranges."""
    indicators = []
    if telemetry.get("latency_ms", 0) > LATENCY_WARNING_MS:
        indicators.append("high_latency")
    if telemetry.get("packet_loss_percent", 0) > PACKET_LOSS_WARNING:
        indicators.append("elevated_packet_loss")
    if telemetry.get("jitter_ms", 0) > JITTER_WARNING_MS:
        indicators.append("high_jitter")
    if telemetry.get("throughput_mbps", 100) < THROUGHPUT_WARNING:
        indicators.append("reduced_throughput")
    if telemetry.get("bandwidth_utilization_percent", 0) > BW_UTIL_WARNING:
        indicators.append("high_bandwidth_utilization")
    if telemetry.get("router_cpu_percent", 0) > CPU_WARNING:
        indicators.append("high_router_cpu")
    if telemetry.get("router_memory_percent", 0) > MEM_WARNING:
        indicators.append("high_router_memory")
    return indicators


def generate_explanation(
    telemetry: Dict[str, Any],
    anomaly_result: Dict[str, Any],
    qoe_result: Dict[str, Any],
    severity: str,
    contributing: List[str],
) -> str:
    """
    Generate a human-readable explanation of the current network state.
    """
    parts = []

    if severity == "HEALTHY":
        parts.append("The ISP network is operating within normal parameters.")
    else:
        indicator_phrases = {
            "high_latency": f"high network latency ({telemetry.get('latency_ms', 0):.1f} ms)",
            "elevated_packet_loss": f"elevated packet loss ({telemetry.get('packet_loss_percent', 0):.2f}%)",
            "high_jitter": f"high jitter ({telemetry.get('jitter_ms', 0):.1f} ms)",
            "reduced_throughput": f"reduced throughput ({telemetry.get('throughput_mbps', 0):.1f} Mbps)",
            "high_bandwidth_utilization": f"high bandwidth utilization ({telemetry.get('bandwidth_utilization_percent', 0):.1f}%)",
            "high_router_cpu": f"high router CPU usage ({telemetry.get('router_cpu_percent', 0):.1f}%)",
            "high_router_memory": f"elevated router memory usage ({telemetry.get('router_memory_percent', 0):.1f}%)",
        }
        phrases = [indicator_phrases[k] for k in contributing if k in indicator_phrases]
        if phrases:
            parts.append("The following network indicators are outside normal ranges: " + ", ".join(phrases) + ".")

    if anomaly_result.get("is_anomaly"):
        parts.append(
            "The Isolation Forest model has classified this observation as anomalous "
            f"(anomaly score: {anomaly_result.get('anomaly_score', 0):.4f})."
        )
    else:
        parts.append("The Isolation Forest model classifies this observation as normal.")

    qoe_class = qoe_result.get("qoe_class", "UNKNOWN")
    parts.append(f"The QoE classifier estimates {qoe_class} customer experience.")

    return " ".join(parts)


def generate_recommendations(
    contributing: List[str],
    severity: str,
    qoe_class: str,
) -> List[str]:
    """
    Generate investigation recommendations based on observed indicators.

    These are suggestions for network administrators to investigate,
    NOT confirmed root causes or automatic repair actions.
    """
    recs = []

    if "high_latency" in contributing:
        recs.append("Investigate routing table for suboptimal paths; check for congestion on backbone links.")
    if "elevated_packet_loss" in contributing:
        recs.append("Examine physical layer errors on uplink interfaces; check for duplex mismatches.")
    if "high_bandwidth_utilization" in contributing:
        recs.append("Review traffic shaping policies; consider load balancing across available links.")
    if "high_router_cpu" in contributing:
        recs.append("Inspect router process utilization; look for routing protocol convergence events.")
    if "high_router_memory" in contributing:
        recs.append("Review router memory allocation; check for large routing table growth or memory leaks.")
    if "reduced_throughput" in contributing:
        recs.append("Correlate throughput reduction with packet loss and bandwidth utilization metrics.")
    if "high_jitter" in contributing:
        recs.append("Check for QoS configuration; prioritize latency-sensitive traffic queues.")

    if severity == "CRITICAL" and not recs:
        recs.append("Critical network state detected. Initiate escalation procedures and review all interface statistics.")
    elif not recs:
        recs.append("Network appears stable. Continue standard monitoring procedures.")

    return recs


def analyze(
    telemetry: Dict[str, Any],
    anomaly_result: Dict[str, Any],
    qoe_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Full AI decision analysis combining all signals.

    Args:
        telemetry: Raw metric snapshot from the simulator.
        anomaly_result: Output from InferenceEngine.predict_anomaly().
        qoe_result: Output from InferenceEngine.predict_qoe().

    Returns:
        Comprehensive network health assessment dictionary.
    """
    health_score  = calculate_health_score(telemetry)
    qoe_class     = qoe_result.get("qoe_class", "UNKNOWN")
    is_anomaly    = anomaly_result.get("is_anomaly", False)
    contributing  = identify_contributing_indicators(telemetry)
    severity      = get_severity(health_score, is_anomaly, qoe_class)
    explanation   = generate_explanation(telemetry, anomaly_result, qoe_result, severity, contributing)
    recommendations = generate_recommendations(contributing, severity, qoe_class)

    return {
        "health_score":           health_score,
        "severity":               severity,
        "is_anomaly":             is_anomaly,
        "anomaly_score":          anomaly_result.get("anomaly_score", 0.0),
        "qoe_class":              qoe_class,
        "qoe_score":              qoe_result.get("qoe_score", -1),
        "contributing_indicators": contributing,
        "explanation":            explanation,
        "recommendations":        recommendations,
        "class_probabilities":    qoe_result.get("class_probabilities", {}),
    }
