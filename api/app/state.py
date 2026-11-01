"""
api/app/state.py
Shared application state accessible across request handlers.
Holds references to the inference engine and latest analysis results.
"""
import asyncio
from collections import deque
from typing import Any, Deque, Dict, Optional

from .ml.inference import InferenceEngine
from .config import settings

# ── Singletons ─────────────────────────────────────────────────────────────────

engine = InferenceEngine(model_dir=settings.ml_model_dir)

# Rolling window of the last 100 predictions (for /anomalies and /predictions)
recent_predictions: Deque[Dict[str, Any]] = deque(maxlen=100)

# Latest complete analysis (updated by background task)
latest_analysis: Optional[Dict[str, Any]] = None

# Latest raw telemetry from the simulator
latest_telemetry: Optional[Dict[str, Any]] = None
