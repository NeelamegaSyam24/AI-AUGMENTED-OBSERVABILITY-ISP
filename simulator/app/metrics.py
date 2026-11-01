"""
simulator/app/metrics.py
Prometheus metrics definitions for the ISP Network Simulator.

All metrics use the `isp_` prefix for consistent namespacing.
"""
from prometheus_client import Gauge, Counter, Histogram

# ── Core network performance metrics ─────────────────────────────────────────

isp_network_latency_ms = Gauge(
    "isp_network_latency_ms",
    "Network round-trip latency in milliseconds (core router → edge router)",
)

isp_network_packet_loss_percent = Gauge(
    "isp_network_packet_loss_percent",
    "Percentage of packets dropped on the network link",
)

isp_network_jitter_ms = Gauge(
    "isp_network_jitter_ms",
    "Network jitter (variation in packet delay) in milliseconds",
)

isp_network_throughput_mbps = Gauge(
    "isp_network_throughput_mbps",
    "Actual network throughput in Megabits per second",
)

isp_bandwidth_utilization_percent = Gauge(
    "isp_bandwidth_utilization_percent",
    "Percentage of total bandwidth capacity currently in use",
)

# ── Error and connection metrics ──────────────────────────────────────────────

isp_network_errors_total = Counter(
    "isp_network_errors_total",
    "Cumulative count of network-level errors (CRC, frame, interface errors)",
)

isp_active_connections = Gauge(
    "isp_active_connections",
    "Number of active subscriber connections currently managed by the gateway",
)

# ── Router resource metrics ────────────────────────────────────────────────────

isp_router_cpu_usage_percent = Gauge(
    "isp_router_cpu_usage_percent",
    "Core router CPU utilization percentage",
)

isp_router_memory_usage_percent = Gauge(
    "isp_router_memory_usage_percent",
    "Core router memory utilization percentage",
)

# ── Availability metric ───────────────────────────────────────────────────────

isp_network_availability_percent = Gauge(
    "isp_network_availability_percent",
    "Estimated network availability percentage (100 = fully available)",
)

# ── Latency histogram (distribution analysis) ─────────────────────────────────

isp_latency_histogram_ms = Histogram(
    "isp_latency_histogram_ms",
    "Distribution of network latency measurements in milliseconds",
    buckets=[5, 10, 20, 30, 50, 75, 100, 130, 160, 200, 300, float("inf")],
)


def update_all_metrics(telemetry: dict) -> None:
    """
    Update all Prometheus gauges/counters with fresh telemetry data.

    Args:
        telemetry: Dictionary containing the latest network metric values.
    """
    latency = telemetry.get("latency_ms", 0.0)
    isp_network_latency_ms.set(latency)
    isp_latency_histogram_ms.observe(latency)

    isp_network_packet_loss_percent.set(telemetry.get("packet_loss_percent", 0.0))
    isp_network_jitter_ms.set(telemetry.get("jitter_ms", 0.0))
    isp_network_throughput_mbps.set(telemetry.get("throughput_mbps", 0.0))
    isp_bandwidth_utilization_percent.set(telemetry.get("bandwidth_utilization_percent", 0.0))
    isp_active_connections.set(telemetry.get("active_connections", 0))
    isp_router_cpu_usage_percent.set(telemetry.get("router_cpu_percent", 0.0))
    isp_router_memory_usage_percent.set(telemetry.get("router_memory_percent", 0.0))
    isp_network_availability_percent.set(telemetry.get("network_availability_percent", 100.0))

    # Increment errors counter only when errors occur (not a reset gauge)
    errors = telemetry.get("network_errors_delta", 0)
    if errors > 0:
        isp_network_errors_total.inc(errors)
