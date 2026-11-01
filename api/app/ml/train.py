"""
api/app/ml/train.py
Model training script for both ML models:
  1. Isolation Forest — anomaly detection
  2. Random Forest Classifier — QoE classification

This script generates a synthetic training dataset based on the documented
ISP scenario definitions, trains both models, evaluates them, and persists
the trained artifacts to the models/ directory.

Training is performed once at container startup (via Dockerfile CMD).
Models are NOT retrained on every API call.

Synthetic QoE label methodology
─────────────────────────────────
Labels are created using domain-driven rules BEFORE model training to avoid
target leakage. The classifier learns to reproduce these rules given the
input features, effectively generalising the boundaries.

GOOD   : latency < 60 ms  AND packet_loss < 1%  AND bandwidth_util < 75%
POOR   : latency > 130 ms OR  packet_loss > 5%  OR  bandwidth_util > 90%
MODERATE : everything else
"""
import os
import json
import logging
import random
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODEL_DIR = Path(os.getenv("ML_MODEL_DIR", "/app/models"))
RANDOM_STATE = int(os.getenv("ANOMALY_RANDOM_STATE", "42"))
N_SAMPLES_PER_SCENARIO = 400   # Total dataset size = 6 scenarios × 400 = 2400 samples


# ── Dataset generation ─────────────────────────────────────────────────────────

def _gauss(mean: float, std: float, lo: float = 0.0, hi: float = float("inf")) -> float:
    """Bounded Gaussian sample."""
    return float(np.clip(random.gauss(mean, std), lo, hi))


SCENARIO_PARAMS = {
    "normal":         dict(lat=20,  pl=0.1,  jit=3,   tp=95,  bw=45,  cpu=40, mem=55),
    "high-latency":   dict(lat=180, pl=1.5,  jit=40,  tp=65,  bw=80,  cpu=65, mem=62),
    "packet-loss":    dict(lat=100, pl=7.5,  jit=35,  tp=45,  bw=85,  cpu=72, mem=68),
    "congestion":     dict(lat=150, pl=4.0,  jit=30,  tp=30,  bw=95,  cpu=78, mem=74),
    "router-overload":dict(lat=130, pl=3.0,  jit=25,  tp=55,  bw=75,  cpu=92, mem=87),
    "recovery":       dict(lat=50,  pl=0.5,  jit=8,   tp=82,  bw=58,  cpu=52, mem=60),
}


def generate_dataset(n_per_scenario: int = N_SAMPLES_PER_SCENARIO) -> pd.DataFrame:
    """
    Generate a synthetic training dataset from all ISP scenarios.

    Returns a DataFrame with feature columns and a 'scenario' column.
    """
    rows = []
    random.seed(RANDOM_STATE)
    np.random.seed(RANDOM_STATE)

    for scenario, p in SCENARIO_PARAMS.items():
        noise = 0.12 if scenario == "normal" else 0.15
        for _ in range(n_per_scenario):
            rows.append({
                "scenario": scenario,
                "latency_ms":                    _gauss(p["lat"], p["lat"]  * noise, 1, 500),
                "packet_loss_percent":            _gauss(p["pl"],  p["pl"]  * noise + 0.05, 0, 100),
                "jitter_ms":                      _gauss(p["jit"], p["jit"] * noise, 0, 200),
                "throughput_mbps":                _gauss(p["tp"],  p["tp"]  * noise, 0.1, 1000),
                "bandwidth_utilization_percent":  _gauss(p["bw"],  p["bw"]  * noise, 0, 100),
                "router_cpu_percent":             _gauss(p["cpu"], p["cpu"] * noise, 0, 100),
                "router_memory_percent":          _gauss(p["mem"], p["mem"] * noise, 0, 100),
            })

    df = pd.DataFrame(rows)
    # Derived feature: network_stress (combine key indicators)
    df["network_stress"] = (
        df["latency_ms"] / 200.0 * 0.3
        + df["packet_loss_percent"] / 10.0 * 0.3
        + df["bandwidth_utilization_percent"] / 100.0 * 0.2
        + df["router_cpu_percent"] / 100.0 * 0.2
    )
    return df


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


def make_qoe_labels(df: pd.DataFrame) -> pd.Series:
    """
    Generate synthetic QoE labels using documented rule-based methodology.

    GOOD     : latency < 60 ms  AND packet_loss < 1%  AND bw_util < 75%
    POOR     : latency > 130 ms OR  packet_loss > 5%  OR  bw_util > 90%
    MODERATE : everything else

    These rules are applied to the raw features BEFORE any model sees them,
    eliminating target leakage.
    """
    labels = []
    for _, row in df.iterrows():
        lat = row["latency_ms"]
        pl  = row["packet_loss_percent"]
        bw  = row["bandwidth_utilization_percent"]

        if lat < 60 and pl < 1.0 and bw < 75.0:
            labels.append("GOOD")
        elif lat > 130 or pl > 5.0 or bw > 90.0:
            labels.append("POOR")
        else:
            labels.append("MODERATE")
    return pd.Series(labels, index=df.index)


# ── Anomaly labels for IsolationForest training reference ─────────────────────

ANOMALOUS_SCENARIOS = {"high-latency", "packet-loss", "congestion", "router-overload"}


# ── Training ──────────────────────────────────────────────────────────────────

def train_anomaly_model(df: pd.DataFrame) -> Tuple[IsolationForest, StandardScaler]:
    """
    Train an Isolation Forest model for unsupervised anomaly detection.

    The model is trained on ALL scenario data (semi-supervised approach).
    The contamination parameter reflects the expected fraction of anomalous
    observations in operational data.

    Returns:
        Tuple of (trained IsolationForest, fitted StandardScaler)
    """
    logger.info("Training Isolation Forest anomaly detector …")
    X = df[FEATURE_COLS].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators=100,
        contamination=float(os.getenv("ANOMALY_CONTAMINATION", "0.1")),
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    # Evaluate against known labels (not used for training — informational only)
    preds = model.predict(X_scaled)   # 1 = normal, -1 = anomaly
    known_anomaly = df["scenario"].isin(ANOMALOUS_SCENARIOS).values
    detected = (preds == -1)
    precision = (detected & known_anomaly).sum() / max(detected.sum(), 1)
    recall    = (detected & known_anomaly).sum() / max(known_anomaly.sum(), 1)
    logger.info(
        "Anomaly model – approx precision=%.3f, recall=%.3f (informational, based on known labels)",
        precision, recall,
    )
    return model, scaler


def train_qoe_model(df: pd.DataFrame) -> Tuple[RandomForestClassifier, LabelEncoder, StandardScaler]:
    """
    Train a Random Forest classifier for QoE estimation.

    Returns:
        Tuple of (trained model, fitted LabelEncoder, fitted StandardScaler)
    """
    logger.info("Training QoE classifier (Random Forest) …")
    df = df.copy()
    df["qoe_label"] = make_qoe_labels(df)

    X = df[FEATURE_COLS].values
    y_raw = df["qoe_label"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    le = LabelEncoder()
    y = le.fit_transform(y_raw)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=le.classes_)
    cm = confusion_matrix(y_test, y_pred)

    logger.info("QoE model accuracy: %.4f", acc)
    logger.info("Classification report:\n%s", report)
    logger.info("Confusion matrix:\n%s", cm)

    return model, le, scaler


# ── Persistence ────────────────────────────────────────────────────────────────

def save_artifacts(
    anomaly_model: IsolationForest,
    anomaly_scaler: StandardScaler,
    qoe_model: RandomForestClassifier,
    qoe_le: LabelEncoder,
    qoe_scaler: StandardScaler,
    df: pd.DataFrame,
) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(anomaly_model,  MODEL_DIR / "anomaly_model.joblib")
    joblib.dump(anomaly_scaler, MODEL_DIR / "anomaly_scaler.joblib")
    joblib.dump(qoe_model,      MODEL_DIR / "qoe_model.joblib")
    joblib.dump(qoe_le,         MODEL_DIR / "qoe_label_encoder.joblib")
    joblib.dump(qoe_scaler,     MODEL_DIR / "qoe_scaler.joblib")

    # Save QoE evaluation metrics
    df_eval = df.copy()
    df_eval["qoe_label"] = make_qoe_labels(df_eval)
    X_scaled = qoe_scaler.transform(df_eval[FEATURE_COLS].values)
    y_true = qoe_le.transform(df_eval["qoe_label"].values)
    y_pred = qoe_model.predict(X_scaled)

    report_dict = classification_report(
        y_true, y_pred,
        target_names=qoe_le.classes_,
        output_dict=True,
    )
    metadata = {
        "feature_columns": FEATURE_COLS,
        "qoe_classes": list(qoe_le.classes_),
        "qoe_class_to_index": {c: int(i) for i, c in enumerate(qoe_le.classes_)},
        "qoe_accuracy": accuracy_score(y_true, y_pred),
        "qoe_report": report_dict,
        "anomaly_contamination": float(os.getenv("ANOMALY_CONTAMINATION", "0.1")),
        "training_samples": len(df),
        "random_state": RANDOM_STATE,
        "qoe_label_rules": {
            "GOOD": "latency_ms < 60 AND packet_loss_percent < 1 AND bandwidth_utilization_percent < 75",
            "POOR": "latency_ms > 130 OR packet_loss_percent > 5 OR bandwidth_utilization_percent > 90",
            "MODERATE": "all other observations",
        },
    }
    with open(MODEL_DIR / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Models and metadata saved to %s", MODEL_DIR)


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    # Skip training if models already exist (allow forced retrain via env var)
    force = os.getenv("FORCE_RETRAIN", "false").lower() == "true"
    if not force and (MODEL_DIR / "anomaly_model.joblib").exists():
        logger.info("Models already exist at %s — skipping training (set FORCE_RETRAIN=true to override)", MODEL_DIR)
        return

    logger.info("=== ISP AI Observability — ML Training ===")

    df = generate_dataset()
    logger.info("Dataset generated: %d rows, %d columns", len(df), len(df.columns))

    anomaly_model, anomaly_scaler = train_anomaly_model(df)
    qoe_model, qoe_le, qoe_scaler = train_qoe_model(df)

    save_artifacts(anomaly_model, anomaly_scaler, qoe_model, qoe_le, qoe_scaler, df)
    logger.info("=== Training complete ===")


if __name__ == "__main__":
    main()
