"""
simulator/app/simulator.py
Core ISP network telemetry simulator.

Generates realistic metric values by applying Gaussian noise around
the scenario target values. Maintains simulation state across intervals.
"""
import random
import time
from typing import Dict, Any, Optional

from .scenarios import ScenarioConfig, SCENARIOS
from .config import settings


class ISPNetworkSimulator:
    """
    Simulates an ISP network by generating telemetry data for a given scenario.

    Metric values vary realistically around scenario targets using
    bounded Gaussian noise. The simulator holds internal state so that
    consecutive readings are plausible.
    """

    def __init__(self) -> None:
        self._current_scenario_name: str = settings.simulator_default_scenario
        self._current_scenario: ScenarioConfig = SCENARIOS[self._current_scenario_name]
        self._last_telemetry: Optional[Dict[str, Any]] = None
        self._start_time: float = time.time()
        random.seed(None)   # Use system entropy (non-deterministic during runtime)

    # ── Scenario management ───────────────────────────────────────────────────

    @property
    def current_scenario_name(self) -> str:
        return self._current_scenario_name

    @property
    def current_scenario(self) -> ScenarioConfig:
        return self._current_scenario

    def set_scenario(self, scenario_name: str) -> ScenarioConfig:
        """
        Switch to the named scenario.

        Args:
            scenario_name: Key from SCENARIOS dict (e.g. 'normal', 'high-latency').

        Returns:
            The activated ScenarioConfig.

        Raises:
            ValueError: If scenario_name is not registered.
        """
        if scenario_name not in SCENARIOS:
            raise ValueError(
                f"Unknown scenario '{scenario_name}'. "
                f"Available: {list(SCENARIOS.keys())}"
            )
        self._current_scenario_name = scenario_name
        self._current_scenario = SCENARIOS[scenario_name]
        return self._current_scenario

    def list_scenarios(self) -> list[str]:
        """Return all registered scenario names."""
        return list(SCENARIOS.keys())

    # ── Telemetry generation ──────────────────────────────────────────────────

    def _add_noise(self, value: float, noise_factor: float, min_val: float = 0.0,
                   max_val: float = float("inf")) -> float:
        """
        Add realistic Gaussian noise to a metric value.

        The noise magnitude scales with the value (proportional noise model),
        which produces naturally larger absolute variation for large metrics.
        """
        sigma = value * noise_factor + 0.1   # Small baseline avoids zero sigma
        noisy = random.gauss(value, sigma)
        return max(min_val, min(max_val, noisy))

    def generate_telemetry(self) -> Dict[str, Any]:
        """
        Generate a single telemetry snapshot for the current scenario.

        Returns:
            Dictionary of metric name → current value mappings.
        """
        sc = self._current_scenario
        nf = sc.noise_factor

        latency = self._add_noise(sc.latency_ms, nf, 1.0, 500.0)
        packet_loss = self._add_noise(sc.packet_loss_percent, nf, 0.0, 100.0)
        jitter = self._add_noise(sc.jitter_ms, nf, 0.0, 200.0)
        throughput = self._add_noise(sc.throughput_mbps, nf, 0.1, 1000.0)
        bw_util = self._add_noise(sc.bandwidth_utilization_percent, nf, 0.0, 100.0)
        cpu = self._add_noise(sc.router_cpu_percent, nf, 0.0, 100.0)
        memory = self._add_noise(sc.router_memory_percent, nf, 0.0, 100.0)
        connections = max(0, int(self._add_noise(sc.active_connections, nf, 0.0)))
        availability = self._add_noise(sc.network_availability_percent, nf * 0.1, 0.0, 100.0)

        # Network errors: Poisson-like distribution around rate
        errors_delta = max(0, int(random.gauss(sc.network_errors_rate, sc.network_errors_rate * 0.3 + 0.1)))

        telemetry = {
            "scenario": self._current_scenario_name,
            "latency_ms": round(latency, 2),
            "packet_loss_percent": round(packet_loss, 4),
            "jitter_ms": round(jitter, 2),
            "throughput_mbps": round(throughput, 2),
            "bandwidth_utilization_percent": round(bw_util, 2),
            "router_cpu_percent": round(cpu, 2),
            "router_memory_percent": round(memory, 2),
            "active_connections": connections,
            "network_errors_delta": errors_delta,
            "network_availability_percent": round(availability, 3),
            "uptime_seconds": round(time.time() - self._start_time, 1),
        }
        self._last_telemetry = telemetry
        return telemetry

    @property
    def last_telemetry(self) -> Optional[Dict[str, Any]]:
        """Return the most recently generated telemetry snapshot."""
        return self._last_telemetry


# ── Singleton instance (shared across FastAPI app) ─────────────────────────────
simulator = ISPNetworkSimulator()
