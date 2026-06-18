"""Carga y persistencia de configuración en JSON."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, TypeVar, get_args, get_type_hints

from config.defaults import get_default_config
from config.schema import AppConfig
from utils.logging import get_logger
from utils.paths import get_config_path

logger = get_logger(__name__)

T = TypeVar("T")


class ConfigManager:
    """Gestiona la configuración persistente de la aplicación."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or get_config_path()
        self._config: AppConfig = get_default_config()

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def path(self) -> Path:
        return self._config_path

    def load(self) -> AppConfig:
        if not self._config_path.exists():
            logger.info("Config not found at %s, using defaults", self._config_path)
            self._config = get_default_config()
            self.save()
            return self._config

        try:
            raw = json.loads(self._config_path.read_text(encoding="utf-8"))
            self._config = _dict_to_dataclass(AppConfig, raw)
            logger.info("Config loaded from %s", self._config_path)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Invalid config file (%s), resetting to defaults", exc)
            self._config = get_default_config()
            self.save()

        return self._config

    def save(self) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._config.to_dict(), indent=2, ensure_ascii=False)
        self._config_path.write_text(payload, encoding="utf-8")
        logger.debug("Config saved to %s", self._config_path)

    def update(self, config: AppConfig) -> None:
        self._config = config
        self.save()


def _dict_to_dataclass(cls: type[T], data: dict[str, Any]) -> T:
    if not is_dataclass(cls):
        raise TypeError(f"{cls} is not a dataclass")

    kwargs: dict[str, Any] = {}
    type_hints = get_type_hints(cls)
    for field_info in fields(cls):
        if field_info.name not in data:
            continue

        value = data[field_info.name]
        field_type = type_hints.get(field_info.name, field_info.type)

        if is_dataclass(field_type) and isinstance(value, dict):
            kwargs[field_info.name] = _dict_to_dataclass(field_type, value)
        elif _is_optional_str(field_type) and value is not None and not isinstance(value, str):
            kwargs[field_info.name] = str(value)
        else:
            kwargs[field_info.name] = value

    return cls(**kwargs)


def _is_optional_str(annotation: Any) -> bool:
    if annotation is str:
        return True
    return str in get_args(annotation)
