"""Rutas de datos de la aplicación en el sistema de archivos."""

from __future__ import annotations

import os
from pathlib import Path

from core.constants import APP_DIR_NAME


def get_app_data_dir() -> Path:
    """Directorio persistente de la aplicación (%APPDATA% en Windows)."""
    base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(base) / APP_DIR_NAME


def get_config_path() -> Path:
    return get_app_data_dir() / "config.json"


def get_database_path() -> Path:
    return get_app_data_dir() / "pokemon.db"


def get_logs_dir() -> Path:
    return get_app_data_dir() / "logs"


def get_exports_dir() -> Path:
    return get_app_data_dir() / "exports"


def get_screenshots_dir() -> Path:
    return get_app_data_dir() / "screenshots"


def ensure_app_directories() -> None:
    """Crea los directorios necesarios si no existen."""
    for directory in (
        get_app_data_dir(),
        get_logs_dir(),
        get_exports_dir(),
        get_screenshots_dir(),
    ):
        directory.mkdir(parents=True, exist_ok=True)
