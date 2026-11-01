"""
simulator/app/config.py
Configuration settings for the ISP Network Simulator.
"""
import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class SimulatorSettings(BaseSettings):
    model_config = ConfigDict(env_file='.env', extra='ignore')
    """Application settings loaded from environment variables."""

    # Server
    simulator_port: int = int(os.getenv("SIMULATOR_PORT", "8001"))
    simulator_interval: float = float(os.getenv("SIMULATOR_INTERVAL", "5"))
    simulator_default_scenario: str = os.getenv("SIMULATOR_DEFAULT_SCENARIO", "normal")

    # Noise level for realistic metric variation
    noise_level: float = 0.05

    # model_config defined above as class variable


settings = SimulatorSettings()
