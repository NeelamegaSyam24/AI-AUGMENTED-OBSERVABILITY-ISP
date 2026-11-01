"""
api/app/config.py
Configuration settings for the FastAPI / ML service.
"""
import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class APISettings(BaseSettings):
    model_config = ConfigDict(env_file='.env', extra='ignore')
    # Server
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    # External service URLs
    simulator_url: str = os.getenv("SIMULATOR_URL", "http://simulator:8001")

    # ML
    ml_model_dir: str = os.getenv("ML_MODEL_DIR", "/app/models")
    anomaly_contamination: float = float(os.getenv("ANOMALY_CONTAMINATION", "0.1"))
    anomaly_random_state: int = int(os.getenv("ANOMALY_RANDOM_STATE", "42"))
    qoe_random_state: int = int(os.getenv("QOE_RANDOM_STATE", "42"))

    # CORS
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")


    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = APISettings()
