"""
Logging configuration for TrafficLens.
Provides structured, readable, and safe logging.
"""

import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure system-wide logging with standard formatting."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    log_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Suppress overly chatty third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
    logging.getLogger("scapy.loading").setLevel(logging.ERROR)

    logger = logging.getLogger("trafficlens")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
