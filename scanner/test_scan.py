"""Escaneo de prueba: captura de pantalla + OCR."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from adb import AdbClient
from config.schema import ScanConfig
from ocr import OcrEngine
from utils.logging import get_logger
from utils.paths import get_screenshots_dir

logger = get_logger(__name__)


@dataclass(slots=True)
class TestScanResult:
    screenshot_path: Path
    device_serial: str
    ocr_text: str
    success: bool
    message: str


def build_screenshot_path(scan_config: ScanConfig) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extension = scan_config.screenshot_format.lstrip(".") or "png"
    return get_screenshots_dir() / f"capture_{timestamp}.{extension}"


def capture_screenshot(adb_client: AdbClient, scan_config: ScanConfig) -> tuple[Path, str]:
    device_serial = adb_client.resolve_device_serial()
    if device_serial is None:
        raise RuntimeError("No hay ningún dispositivo Android listo.")

    screenshot_path = build_screenshot_path(scan_config)
    adb_client.capture_screenshot(screenshot_path, serial=device_serial)
    return screenshot_path, device_serial


def run_test_scan(
    adb_client: AdbClient,
    ocr_engine: OcrEngine,
    scan_config: ScanConfig,
) -> TestScanResult:
    screenshot_path, device_serial = capture_screenshot(adb_client, scan_config)

    try:
        ocr_text = ocr_engine.extract_text(screenshot_path)
    except Exception as exc:
        logger.exception("OCR failed during test scan")
        return TestScanResult(
            screenshot_path=screenshot_path,
            device_serial=device_serial,
            ocr_text="",
            success=False,
            message=f"Captura guardada, pero OCR falló: {exc}",
        )

    if not ocr_text.strip():
        return TestScanResult(
            screenshot_path=screenshot_path,
            device_serial=device_serial,
            ocr_text="",
            success=False,
            message="Captura guardada, pero no se detectó texto.",
        )

    return TestScanResult(
        screenshot_path=screenshot_path,
        device_serial=device_serial,
        ocr_text=ocr_text,
        success=True,
        message="Escaneo de prueba completado.",
    )
