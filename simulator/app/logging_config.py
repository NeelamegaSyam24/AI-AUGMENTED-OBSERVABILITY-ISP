"""
simulator/app/logging_config.py
Structured logging configuration for the simulator.
"""
import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure application-wide logging with a structured format."""
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("prometheus_client").setLevel(logging.WARNING)
