"""Punto de entrada principal de Pokemon GO Box Manager."""

from __future__ import annotations

import sys
from pathlib import Path

# Permite ejecutar también con `python app\main.py` desde la raíz del proyecto.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import ConfigManager
from core.constants import APP_NAME, APP_VERSION
from database import init_database
from ui import run_app
from utils import ensure_app_directories, get_database_path, get_logger, setup_logging


def main() -> int:
    ensure_app_directories()

    config_manager = ConfigManager()
    app_config = config_manager.load()

    setup_logging(level=app_config.log_level)
    logger = get_logger(__name__)
    logger.info("Starting %s v%s", APP_NAME, APP_VERSION)

    init_database(get_database_path())
    logger.info("Launching main window")
    return run_app(config_manager)


if __name__ == "__main__":
    sys.exit(main())
