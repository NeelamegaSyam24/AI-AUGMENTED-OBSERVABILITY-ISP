# ML Methodology

## Overview

This document describes the machine learning methodology used in the AI-Augmented ISP Observability System.

---

## Dataset Generation

### Source
Synthetic data generated from 6 ISP network scenarios (NORMAL, HIGH_LATENCY, PACKET_LOSS, CONGESTION, ROUTER_OVERLOAD, RECOVERY).

### Sample Size
- 400 samples per scenario × 6 scenarios = **2,400 total training samples**
- Each sample is generated with Gaussian noise applied to the scenario target values

### Feature Columns

| Feature | Description | Range |
|---------|-------------|-------|
| `latency_ms` | Round-trip latency in milliseconds | 1–500 ms |
| `packet_loss_percent` | Percentage of dropped packets | 0–100% |
| `jitter_ms` | Packet delay variation | 0–200 ms |
| `throughput_mbps` | Data transfer rate | 0.1–1000 Mbps |
| `bandwidth_utilization_percent` | Link capacity in use | 0–100% |
| `router_cpu_percent` | Core router CPU usage | 0–100% |
| `router_memory_percent` | Core router memory usage | 0–100% |
| `network_stress` | Derived composite indicator | 0–1 |

### Derived Feature: network_stress

```
network_stress = (latency_ms/200 × 0.3) + (packet_loss_percent/10 × 0.3)
              + (bandwidth_utilization_percent/100 × 0.2)
              + (router_cpu_percent/100 × 0.2)
```

This captures aggregate network pressure in a single normalized value.

---

## Model 1: Isolation Forest (Anomaly Detection)

### Algorithm
`sklearn.ensemble.IsolationForest`

### Type
Unsupervised anomaly detection — no labels required during training.

### Rationale
- Does not require labeled anomaly examples (rare in operations)
- Handles multi-dimensional feature spaces efficiently
- Linear time complexity O(n log n)
- Produces an interpretable anomaly score

### Key Parameters
- `n_estimators=100` — Number of isolation trees
- `contamination=0.1` — Expected anomaly fraction in operational data
- `random_state=42` — Reproducible results

### Training Procedure
1. All 2,400 samples are used (semi-supervised: includes both normal and anomalous scenarios)
2. Features are scaled with `StandardScaler` (zero mean, unit variance)
3. The model learns the data distribution from the training set
4. A threshold is set automatically based on contamination parameter

### Inference
- Input: 8-feature scaled vector
- `predict()` returns: 1 (normal) or -1 (anomaly)
- `score_samples()` returns: raw anomaly score (more negative = more anomalous)

### ⚠️ Score Interpretation
The anomaly score is NOT a probability. It is a relative measure of isolation:
- Score near 0 → normal (hard to isolate)
- Score below -0.1 → potentially anomalous
- Score below -0.2 → strongly anomalous

### Informational Evaluation
Using known scenario labels (not used for training):
- Anomalous scenarios: HIGH_LATENCY, PACKET_LOSS, CONGESTION, ROUTER_OVERLOAD
- Normal scenarios: NORMAL, RECOVERY
- Results are informational only — the model is unsupervised

---

## Model 2: Random Forest Classifier (QoE Estimation)

### Algorithm
`sklearn.ensemble.RandomForestClassifier`

### Type
Supervised multi-class classification

### QoE Classes
| Class | Numeric Score | Prometheus Value |
|-------|--------------|-----------------|
| GOOD | 2 | 2 |
| MODERATE | 1 | 1 |
| POOR | 0 | 0 |

### Synthetic Label Methodology

Labels are generated BEFORE model training using domain-driven rules:

```python
if latency_ms < 60 AND packet_loss_percent < 1.0 AND bandwidth_utilization_percent < 75.0:
    label = "GOOD"
elif latency_ms > 130 OR packet_loss_percent > 5.0 OR bandwidth_utilization_percent > 90.0:
    label = "POOR"
else:
    label = "MODERATE"
```

**Target Leakage Prevention**: Label generation is completely independent of the feature pipeline and model training.

### Key Parameters
- `n_estimators=100` — Number of decision trees
- `max_depth=10` — Prevents overfitting
- `random_state=42` — Reproducible results

### Training Procedure
1. Generate QoE labels for all 2,400 samples using the rule-based function
2. Scale features with a separate `StandardScaler`
3. Encode labels with `LabelEncoder`
4. Split 80/20 train/test with stratification
5. Train Random Forest on training split
6. Evaluate on held-out test split

### Model Evaluation Metrics
All metrics saved to `model_metadata.json`:
- **Accuracy** — Overall classification rate on test set
- **Precision** — Per-class (GOOD, MODERATE, POOR)
- **Recall** — Per-class
- **F1-Score** — Per-class harmonic mean
- **Confusion Matrix** — 3×3 matrix of actual vs. predicted

### Output
- Primary output: QoE class string (GOOD/MODERATE/POOR)
- Per-class probabilities from `predict_proba()`
- Numeric score for Prometheus gauge

---

## Model Persistence

All artifacts saved to `/app/models/`:
| File | Contents |
|------|----------|
| `anomaly_model.joblib` | Trained IsolationForest |
| `anomaly_scaler.joblib` | StandardScaler for anomaly features |
| `qoe_model.joblib` | Trained RandomForestClassifier |
| `qoe_label_encoder.joblib` | LabelEncoder for QoE classes |
| `qoe_scaler.joblib` | StandardScaler for QoE features |
| `model_metadata.json` | Training parameters, evaluation metrics, label rules |

### Retraining
Models are trained once at container startup. To force retrain:
```powershell
docker compose exec api sh -c "FORCE_RETRAIN=true python -m app.ml.train"
```

---

## Limitations

1. **Synthetic data**: Models trained on simulated distributions, not real ISP traffic
2. **QoE approximation**: Labels are technical proxies, not actual customer satisfaction
3. **Temporal independence**: Each observation is treated independently; temporal patterns are not modeled
4. **Fixed features**: Changing the feature set requires retraining
5. **No calibration**: Isolation Forest scores are not calibrated probabilities
6. **Scale dependency**: Models must be retrained if metric ranges change significantly
