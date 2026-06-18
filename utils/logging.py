"""Configuración centralizada de logging."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from core.constants import APP_NAME
from utils.paths import get_logs_dir

_CONFIGURED = False
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO", log_to_console: bool = True) -> None:
    """Inicializa el sistema de logs (idempotente)."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_dir = get_logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.handlers.clear()

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    logging.getLogger(__name__).info("%s logging initialized", APP_NAME)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger con nombre de módulo."""
    return logging.getLogger(name)
