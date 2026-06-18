"""Esquemas tipados de configuración."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class AdbConfig:
    adb_path: str = "adb"
    scrcpy_path: str = "scrcpy"
    device_serial: str | None = None
    connection_timeout_seconds: float = 10.0


@dataclass(slots=True)
class OcrConfig:
    language: str = "en"
    use_gpu: bool = False
    confidence_threshold: float = 0.6


@dataclass(slots=True)
class ScanConfig:
    delay_between_pokemon_ms: int = 500
    screenshot_format: str = "png"
    max_scroll_attempts: int = 200


@dataclass(slots=True)
class UiConfig:
    theme: str = "dark"
    appearance_mode: str = "dark"
    color_theme: str = "blue"
    window_width: int = 1280
    window_height: int = 800


@dataclass(slots=True)
class AppConfig:
    """Configuración raíz de la aplicación."""

    log_level: str = "INFO"
    database_filename: str = "pokemon.db"
    adb: AdbConfig = field(default_factory=AdbConfig)
    ocr: OcrConfig = field(default_factory=OcrConfig)
    scan: ScanConfig = field(default_factory=ScanConfig)
    ui: UiConfig = field(default_factory=UiConfig)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
