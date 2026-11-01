"""
tests/unit/test_simulator.py
Unit tests for the ISP Network Simulator.
"""
import pytest
from app.simulator import ISPNetworkSimulator
from app.scenarios import SCENARIOS


class TestISPNetworkSimulator:

    def setup_method(self):
        self.sim = ISPNetworkSimulator()

    def test_default_scenario_is_normal(self):
        assert self.sim.current_scenario_name == "normal"

    def test_generates_telemetry(self):
        tel = self.sim.generate_telemetry()
        assert isinstance(tel, dict)
        assert "latency_ms" in tel
        assert "packet_loss_percent" in tel
        assert "jitter_ms" in tel
        assert "throughput_mbps" in tel
        assert "bandwidth_utilization_percent" in tel
        assert "router_cpu_percent" in tel
        assert "router_memory_percent" in tel
        assert "active_connections" in tel

    def test_latency_is_positive(self):
        for _ in range(10):
            tel = self.sim.generate_telemetry()
            assert tel["latency_ms"] > 0

    def test_packet_loss_in_range(self):
        for _ in range(10):
            tel = self.sim.generate_telemetry()
            assert 0 <= tel["packet_loss_percent"] <= 100

    def test_scenario_switch_changes_values(self):
        self.sim.set_scenario("normal")
        normal_latency = [self.sim.generate_telemetry()["latency_ms"] for _ in range(5)]

        self.sim.set_scenario("high-latency")
        high_latency = [self.sim.generate_telemetry()["latency_ms"] for _ in range(5)]

        # High latency scenario should produce higher mean latency
        assert sum(high_latency) / len(high_latency) > sum(normal_latency) / len(normal_latency)

    def test_all_scenarios_available(self):
        expected = {"normal", "high-latency", "packet-loss", "congestion", "router-overload", "recovery"}
        assert expected.issubset(set(self.sim.list_scenarios()))

    def test_invalid_scenario_raises(self):
        with pytest.raises(ValueError):
            self.sim.set_scenario("nonexistent-scenario-xyz")

    def test_last_telemetry_stored(self):
        self.sim.generate_telemetry()
        assert self.sim.last_telemetry is not None

    def test_router_overload_has_high_cpu(self):
        self.sim.set_scenario("router-overload")
        cpu_values = [self.sim.generate_telemetry()["router_cpu_percent"] for _ in range(10)]
        mean_cpu = sum(cpu_values) / len(cpu_values)
        assert mean_cpu > 70, f"Expected high CPU in router-overload, got mean={mean_cpu:.1f}"

    def test_packet_loss_scenario_has_high_loss(self):
        self.sim.set_scenario("packet-loss")
        pl_values = [self.sim.generate_telemetry()["packet_loss_percent"] for _ in range(10)]
        mean_pl = sum(pl_values) / len(pl_values)
        assert mean_pl > 3, f"Expected high packet loss, got mean={mean_pl:.2f}"


class TestScenarioConfigs:
    def test_all_scenarios_have_required_fields(self):
        required = ["latency_ms", "packet_loss_percent", "jitter_ms",
                    "throughput_mbps", "bandwidth_utilization_percent",
                    "router_cpu_percent", "router_memory_percent"]
        for name, sc in SCENARIOS.items():
            for field in required:
                assert hasattr(sc, field), f"Scenario {name} missing field {field}"

    def test_normal_scenario_has_low_latency(self):
        sc = SCENARIOS["normal"]
        assert sc.latency_ms < 40

    def test_recovery_is_marked(self):
        sc = SCENARIOS["recovery"]
        assert sc.is_recovery is True
