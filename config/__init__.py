"""Módulo de configuración."""

from config.manager import ConfigManager
from config.schema import AdbConfig, AppConfig, OcrConfig, ScanConfig, UiConfig

__all__ = [
    "AdbConfig",
    "AppConfig",
    "ConfigManager",
    "OcrConfig",
    "ScanConfig",
    "UiConfig",
]
