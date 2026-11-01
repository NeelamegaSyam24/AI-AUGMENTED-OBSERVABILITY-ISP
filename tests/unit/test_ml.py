"""
tests/unit/test_ml.py
Unit tests for ML decision engine, health scoring, and dataset generation.
Imports api/app modules directly using importlib to avoid path conflicts.
"""
import sys
import os
import importlib.util
import pytest

# ── Load api modules without namespace conflicts ──────────────────────────────
API_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'api'))

def _load(relative_path, module_name):
    """Load a module from an absolute file path under api/."""
    spec = importlib.util.spec_from_file_location(
        module_name,
        os.path.join(API_ROOT, relative_path),
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

# Load decision engine (pure Python, no FastAPI dependency)
de = _load("app/ml/decision_engine.py", "decision_engine_test")

calculate_health_score       = de.calculate_health_score
get_severity                 = de.get_severity
identify_contributing_indicators = de.identify_contributing_indicators
generate_explanation         = de.generate_explanation
generate_recommendations     = de.generate_recommendations
analyze                      = de.analyze

# ── Test data ─────────────────────────────────────────────────────────────────

NORMAL_TELEMETRY = {
    "latency_ms": 20.0,
    "packet_loss_percent": 0.1,
    "jitter_ms": 3.0,
    "throughput_mbps": 95.0,
    "bandwidth_utilization_percent": 45.0,
    "router_cpu_percent": 40.0,
    "router_memory_percent": 55.0,
}

HIGH_LATENCY_TELEMETRY = {
    "latency_ms": 180.0,
    "packet_loss_percent": 1.5,
    "jitter_ms": 40.0,
    "throughput_mbps": 65.0,
    "bandwidth_utilization_percent": 80.0,
    "router_cpu_percent": 65.0,
    "router_memory_percent": 62.0,
}

CRITICAL_TELEMETRY = {
    "latency_ms": 200.0,
    "packet_loss_percent": 8.0,
    "jitter_ms": 50.0,
    "throughput_mbps": 25.0,
    "bandwidth_utilization_percent": 96.0,
    "router_cpu_percent": 93.0,
    "router_memory_percent": 89.0,
}


# ── Health score tests ────────────────────────────────────────────────────────

class TestHealthScore:
    def test_normal_has_high_score(self):
        score = calculate_health_score(NORMAL_TELEMETRY)
        assert score >= 80, f"Normal telemetry should have high health, got {score}"

    def test_critical_has_low_score(self):
        score = calculate_health_score(CRITICAL_TELEMETRY)
        assert score <= 40, f"Critical telemetry should have low health, got {score}"

    def test_score_in_range(self):
        for tel in [NORMAL_TELEMETRY, HIGH_LATENCY_TELEMETRY, CRITICAL_TELEMETRY]:
            score = calculate_health_score(tel)
            assert 0 <= score <= 100, f"Health score out of range: {score}"

    def test_empty_telemetry_returns_number(self):
        score = calculate_health_score({})
        assert isinstance(score, float)


# ── Severity tests ────────────────────────────────────────────────────────────

class TestSeverity:
    def test_healthy_severity(self):
        assert get_severity(90, False, "GOOD") == "HEALTHY"

    def test_warning_by_low_score(self):
        assert get_severity(60, False, "GOOD") == "WARNING"

    def test_critical_by_very_low_score(self):
        assert get_severity(30, False, "POOR") == "CRITICAL"

    def test_warning_by_anomaly(self):
        sev = get_severity(85, True, "GOOD")
        assert sev in ("WARNING", "CRITICAL")

    def test_critical_by_anomaly_and_poor_qoe(self):
        assert get_severity(80, True, "POOR") == "CRITICAL"


# ── Contributing indicators tests ─────────────────────────────────────────────

class TestContributingIndicators:
    def test_normal_has_no_indicators(self):
        indicators = identify_contributing_indicators(NORMAL_TELEMETRY)
        assert len(indicators) == 0

    def test_critical_has_multiple_indicators(self):
        indicators = identify_contributing_indicators(CRITICAL_TELEMETRY)
        assert len(indicators) >= 3

    def test_high_latency_detected(self):
        indicators = identify_contributing_indicators(HIGH_LATENCY_TELEMETRY)
        assert "high_latency" in indicators

    def test_high_bandwidth_detected(self):
        tel = {**NORMAL_TELEMETRY, "bandwidth_utilization_percent": 92.0}
        indicators = identify_contributing_indicators(tel)
        assert "high_bandwidth_utilization" in indicators


# ── Analyze function tests ────────────────────────────────────────────────────

class TestAnalyze:
    def test_analyze_returns_required_keys(self):
        result = analyze(
            NORMAL_TELEMETRY,
            {"is_anomaly": False, "anomaly_score": 0.1},
            {"qoe_class": "GOOD", "qoe_score": 2, "class_probabilities": {}},
        )
        for key in ["health_score", "severity", "is_anomaly", "qoe_class",
                    "explanation", "recommendations", "contributing_indicators"]:
            assert key in result, f"Missing key: {key}"

    def test_explanation_is_non_empty_string(self):
        result = analyze(
            NORMAL_TELEMETRY,
            {"is_anomaly": False, "anomaly_score": 0.1},
            {"qoe_class": "GOOD", "qoe_score": 2, "class_probabilities": {}},
        )
        assert isinstance(result["explanation"], str)
        assert len(result["explanation"]) > 0

    def test_recommendations_are_list(self):
        result = analyze(
            CRITICAL_TELEMETRY,
            {"is_anomaly": True, "anomaly_score": -0.15},
            {"qoe_class": "POOR", "qoe_score": 0, "class_probabilities": {}},
        )
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0

    def test_anomaly_reflected_in_analysis(self):
        result = analyze(
            CRITICAL_TELEMETRY,
            {"is_anomaly": True, "anomaly_score": -0.2},
            {"qoe_class": "POOR", "qoe_score": 0, "class_probabilities": {}},
        )
        assert result["is_anomaly"] is True
        assert result["severity"] == "CRITICAL"


# ── Dataset generation tests ──────────────────────────────────────────────────

class TestDatasetGeneration:
    def setup_method(self):
        """Load train module dynamically."""
        self.train = _load("app/ml/train.py", "train_test")

    def test_generate_dataset_shape(self):
        df = self.train.generate_dataset(n_per_scenario=20)
        assert len(df) == 20 * 6, f"Expected 120 rows, got {len(df)}"

    def test_generate_dataset_has_feature_cols(self):
        df = self.train.generate_dataset(n_per_scenario=10)
        for col in self.train.FEATURE_COLS:
            assert col in df.columns, f"Missing column: {col}"

    def test_qoe_labels_valid_classes(self):
        df = self.train.generate_dataset(n_per_scenario=20)
        labels = self.train.make_qoe_labels(df)
        assert set(labels.unique()).issubset({"GOOD", "MODERATE", "POOR"})

    def test_qoe_labels_length_matches(self):
        df = self.train.generate_dataset(n_per_scenario=20)
        labels = self.train.make_qoe_labels(df)
        assert len(labels) == len(df)

    def test_network_stress_feature_present(self):
        df = self.train.generate_dataset(n_per_scenario=10)
        assert "network_stress" in df.columns

    def test_latency_positive(self):
        df = self.train.generate_dataset(n_per_scenario=10)
        assert (df["latency_ms"] > 0).all()

    def test_packet_loss_in_range(self):
        df = self.train.generate_dataset(n_per_scenario=10)
        assert (df["packet_loss_percent"] >= 0).all()
        assert (df["packet_loss_percent"] <= 100).all()
