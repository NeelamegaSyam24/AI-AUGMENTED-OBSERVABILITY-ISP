"""
tests/integration/test_api.py
Integration tests for the FastAPI endpoints.
Requires the API server to be running at http://localhost:8000.
"""
import pytest
import requests

BASE = "http://localhost:8000"


def api_available():
    try:
        resp = requests.get(f"{BASE}/health", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


skip_if_no_api = pytest.mark.skipif(
    not api_available(),
    reason="API server not running at localhost:8000"
)


@skip_if_no_api
class TestHealthEndpoint:
    def test_health_returns_200(self):
        resp = requests.get(f"{BASE}/health")
        assert resp.status_code == 200

    def test_health_returns_status_healthy(self):
        resp = requests.get(f"{BASE}/health")
        data = resp.json()
        assert data["status"] == "healthy"


@skip_if_no_api
class TestNetworkEndpoints:
    def test_network_health_endpoint(self):
        resp = requests.get(f"{BASE}/network-health")
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "health_score" in data
            assert "severity" in data

    def test_qoe_endpoint(self):
        resp = requests.get(f"{BASE}/qoe")
        assert resp.status_code in (200, 503)

    def test_anomalies_endpoint(self):
        resp = requests.get(f"{BASE}/anomalies")
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "anomalies" in data

    def test_predictions_endpoint(self):
        resp = requests.get(f"{BASE}/predictions")
        assert resp.status_code == 200

    def test_events_endpoint(self):
        resp = requests.get(f"{BASE}/events")
        assert resp.status_code == 200

    def test_scenarios_endpoint(self):
        resp = requests.get(f"{BASE}/scenarios")
        assert resp.status_code in (200, 502)

    def test_metrics_endpoint(self):
        resp = requests.get(f"{BASE}/metrics")
        assert resp.status_code == 200
        assert "isp_ai" in resp.text

    def test_docs_endpoint(self):
        resp = requests.get(f"{BASE}/docs")
        assert resp.status_code == 200


@skip_if_no_api
class TestPredictionEndpoints:
    SAMPLE_TELEMETRY = {
        "latency_ms": 180.0,
        "packet_loss_percent": 3.0,
        "jitter_ms": 35.0,
        "throughput_mbps": 50.0,
        "bandwidth_utilization_percent": 88.0,
        "router_cpu_percent": 75.0,
        "router_memory_percent": 70.0,
    }

    def test_predict_anomaly(self):
        resp = requests.post(f"{BASE}/predict/anomaly", json=self.SAMPLE_TELEMETRY)
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "result" in data
            assert "is_anomaly" in data["result"]

    def test_predict_qoe(self):
        resp = requests.post(f"{BASE}/predict/qoe", json=self.SAMPLE_TELEMETRY)
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "result" in data
            assert "qoe_class" in data["result"]
            assert data["result"]["qoe_class"] in ("GOOD", "MODERATE", "POOR")


@skip_if_no_api
class TestScenarioEndpoints:
    def test_activate_normal_scenario(self):
        resp = requests.post(f"{BASE}/scenario/normal")
        assert resp.status_code in (200, 502)

    def test_activate_high_latency(self):
        resp = requests.post(f"{BASE}/scenario/high-latency")
        assert resp.status_code in (200, 502)
