"""
simulator/app/scenarios.py
ISP network scenario definitions.

Each scenario describes a realistic ISP network state with characteristic
metric ranges. Noise is applied during telemetry generation to produce
realistic variation rather than static constant values.
"""
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class ScenarioConfig:
    """Configuration for a single ISP network scenario."""
    name: str
    display_name: str
    description: str
    # Metric target values (mean values; noise is added during generation)
    latency_ms: float
    packet_loss_percent: float
    jitter_ms: float
    throughput_mbps: float
    bandwidth_utilization_percent: float
    router_cpu_percent: float
    router_memory_percent: float
    active_connections: int
    network_errors_rate: float       # errors per interval (for counter)
    network_availability_percent: float
    # Recovery scenario applies gradual return to normal
    is_recovery: bool = False
    # Noise multiplier — higher in degraded scenarios
    noise_factor: float = 0.05


# ── Scenario Registry ─────────────────────────────────────────────────────────

SCENARIOS: Dict[str, ScenarioConfig] = {

    "normal": ScenarioConfig(
        name="normal",
        display_name="Normal Operation",
        description="ISP network operating under normal load conditions.",
        latency_ms=20.0,
        packet_loss_percent=0.1,
        jitter_ms=3.0,
        throughput_mbps=95.0,
        bandwidth_utilization_percent=45.0,
        router_cpu_percent=40.0,
        router_memory_percent=55.0,
        active_connections=2500,
        network_errors_rate=0.5,
        network_availability_percent=99.9,
        noise_factor=0.04,
    ),

    "high-latency": ScenarioConfig(
        name="high-latency",
        display_name="High Latency",
        description="Elevated network latency due to congestion or routing issues.",
        latency_ms=180.0,
        packet_loss_percent=1.5,
        jitter_ms=40.0,
        throughput_mbps=65.0,
        bandwidth_utilization_percent=80.0,
        router_cpu_percent=65.0,
        router_memory_percent=62.0,
        active_connections=2400,
        network_errors_rate=3.0,
        network_availability_percent=97.5,
        noise_factor=0.08,
    ),

    "packet-loss": ScenarioConfig(
        name="packet-loss",
        display_name="Packet Loss",
        description="Significant packet loss affecting network reliability.",
        latency_ms=100.0,
        packet_loss_percent=7.5,
        jitter_ms=35.0,
        throughput_mbps=45.0,
        bandwidth_utilization_percent=85.0,
        router_cpu_percent=72.0,
        router_memory_percent=68.0,
        active_connections=2100,
        network_errors_rate=8.0,
        network_availability_percent=94.0,
        noise_factor=0.10,
    ),

    "congestion": ScenarioConfig(
        name="congestion",
        display_name="Bandwidth Congestion",
        description="Network bandwidth near saturation causing service degradation.",
        latency_ms=150.0,
        packet_loss_percent=4.0,
        jitter_ms=30.0,
        throughput_mbps=30.0,
        bandwidth_utilization_percent=95.0,
        router_cpu_percent=78.0,
        router_memory_percent=74.0,
        active_connections=2800,
        network_errors_rate=5.0,
        network_availability_percent=95.5,
        noise_factor=0.07,
    ),

    "router-overload": ScenarioConfig(
        name="router-overload",
        display_name="Router Overload",
        description="Core router experiencing CPU and memory pressure.",
        latency_ms=130.0,
        packet_loss_percent=3.0,
        jitter_ms=25.0,
        throughput_mbps=55.0,
        bandwidth_utilization_percent=75.0,
        router_cpu_percent=92.0,
        router_memory_percent=87.0,
        active_connections=2600,
        network_errors_rate=6.0,
        network_availability_percent=96.0,
        noise_factor=0.06,
    ),

    "recovery": ScenarioConfig(
        name="recovery",
        display_name="Network Recovery",
        description="Network metrics gradually recovering toward normal values.",
        latency_ms=50.0,
        packet_loss_percent=0.5,
        jitter_ms=8.0,
        throughput_mbps=82.0,
        bandwidth_utilization_percent=58.0,
        router_cpu_percent=52.0,
        router_memory_percent=60.0,
        active_connections=2450,
        network_errors_rate=1.0,
        network_availability_percent=99.0,
        is_recovery=True,
        noise_factor=0.05,
    ),
}
