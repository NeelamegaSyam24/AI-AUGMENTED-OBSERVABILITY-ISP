"""
api/app/ml/inference.py
ML inference engine: loads trained models and runs predictions on telemetry.

Handles:
  - Model loading with graceful fallback.
  - Isolation Forest anomaly detection.
  - Random Forest QoE classification.
  - Combined prediction result.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder

logger = logging.getLogger(__name__)

FEATURE_COLS = [
    "latency_ms",
    "packet_loss_percent",
    "jitter_ms",
    "throughput_mbps",
    "bandwidth_utilization_percent",
    "router_cpu_percent",
    "router_memory_percent",
    "network_stress",
]


class InferenceEngine:
    """Loads and executes both ML models."""

    def __init__(self, model_dir: str) -> None:
        self._model_dir = Path(model_dir)
        self._anomaly_model: Optional[IsolationForest] = None
        self._anomaly_scaler: Optional[StandardScaler] = None
        self._qoe_model: Optional[RandomForestClassifier] = None
        self._qoe_le: Optional[LabelEncoder] = None
        self._qoe_scaler: Optional[StandardScaler] = None
        self._metadata: Dict[str, Any] = {}
        self._loaded: bool = False

    def load(self) -> bool:
        """Load all model artifacts from disk. Returns True on success."""
        try:
            self._anomaly_model  = joblib.load(self._model_dir / "anomaly_model.joblib")
            self._anomaly_scaler = joblib.load(self._model_dir / "anomaly_scaler.joblib")
            self._qoe_model      = joblib.load(self._model_dir / "qoe_model.joblib")
            self._qoe_le         = joblib.load(self._model_dir / "qoe_label_encoder.joblib")
            self._qoe_scaler     = joblib.load(self._model_dir / "qoe_scaler.joblib")
            meta_path = self._model_dir / "model_metadata.json"
            if meta_path.exists():
                with open(meta_path) as f:
                    self._metadata = json.load(f)
            self._loaded = True
            logger.info("ML models loaded from %s", self._model_dir)
            return True
        except Exception as exc:
            logger.error("Failed to load models: %s", exc)
            self._loaded = False
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def _build_feature_vector(self, telemetry: Dict[str, Any]) -> np.ndarray:
        """Extract and compute feature vector from raw telemetry."""
        lat  = float(telemetry.get("latency_ms", 0))
        pl   = float(telemetry.get("packet_loss_percent", 0))
        jit  = float(telemetry.get("jitter_ms", 0))
        tp   = float(telemetry.get("throughput_mbps", 0))
        bw   = float(telemetry.get("bandwidth_utilization_percent", 0))
        cpu  = float(telemetry.get("router_cpu_percent", 0))
        mem  = float(telemetry.get("router_memory_percent", 0))

        # Derived feature (must match training)
        stress = (
            lat / 200.0 * 0.3
            + pl / 10.0 * 0.3
            + bw / 100.0 * 0.2
            + cpu / 100.0 * 0.2
        )
        return np.array([[lat, pl, jit, tp, bw, cpu, mem, stress]])

    def predict_anomaly(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Isolation Forest on telemetry.

        Returns:
            dict with keys:
              is_anomaly (bool)       — True if flagged as anomalous
              anomaly_score (float)   — Raw IF score; more negative = more anomalous
              raw_prediction (int)    — -1 (anomaly) or 1 (normal)
        """
        if not self._loaded:
            return {"is_anomaly": False, "anomaly_score": 0.0, "raw_prediction": 1, "error": "model not loaded"}

        X = self._build_feature_vector(telemetry)
        X_scaled = self._anomaly_scaler.transform(X)

        raw = int(self._anomaly_model.predict(X_scaled)[0])          # 1 or -1
        score = float(self._anomaly_model.score_samples(X_scaled)[0])  # Higher = more normal

        return {
            "is_anomaly": raw == -1,
            "anomaly_score": round(score, 6),
            "raw_prediction": raw,
        }

    def predict_qoe(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run QoE Random Forest classifier on telemetry.

        Returns:
            dict with keys:
              qoe_class (str)          — "GOOD" | "MODERATE" | "POOR"
              qoe_score (int)          — 2=GOOD, 1=MODERATE, 0=POOR (for Prometheus)
              class_probabilities (dict) — per-class probabilities
        """
        if not self._loaded:
            return {"qoe_class": "UNKNOWN", "qoe_score": -1, "class_probabilities": {}, "error": "model not loaded"}

        X = self._build_feature_vector(telemetry)
        X_scaled = self._qoe_scaler.transform(X)

        pred_idx = int(self._qoe_model.predict(X_scaled)[0])
        proba = self._qoe_model.predict_proba(X_scaled)[0]
        qoe_class = self._qoe_le.inverse_transform([pred_idx])[0]

        class_proba = {
            cls: round(float(p), 4)
            for cls, p in zip(self._qoe_le.classes_, proba)
        }

        # Numeric score for Prometheus: GOOD=2, MODERATE=1, POOR=0
        score_map = {"GOOD": 2, "MODERATE": 1, "POOR": 0}
        qoe_score = score_map.get(qoe_class, -1)

        return {
            "qoe_class": qoe_class,
            "qoe_score": qoe_score,
            "class_probabilities": class_proba,
        }

    def predict_all(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Run both models and return combined results."""
        anomaly = self.predict_anomaly(telemetry)
        qoe     = self.predict_qoe(telemetry)
        return {"anomaly": anomaly, "qoe": qoe}
