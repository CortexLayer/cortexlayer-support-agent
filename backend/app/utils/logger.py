"""For logging info."""

import logging
import sys

from backend.app.core.config import settings


def setup_logger(name: str) -> logging.Logger:
    """Create and configure a logger instance for the application."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    format_style = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(format_style)
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger


logger = setup_logger("cortexlayer")
