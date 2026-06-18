"""Valores por defecto de configuración."""

from config.schema import AppConfig


def get_default_config() -> AppConfig:
    return AppConfig()
