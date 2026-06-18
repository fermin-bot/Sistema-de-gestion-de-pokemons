"""Cliente ADB para detectar dispositivos Android."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from config.schema import AdbConfig
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class AdbDevice:
    serial: str
    state: str
    model: str | None = None
    product: str | None = None


class AdbClient:
    def __init__(self, config: AdbConfig) -> None:
        self._config = config

    @property
    def adb_path(self) -> str:
        return self._config.adb_path

    def is_available(self) -> bool:
        executable = shutil.which(self._config.adb_path)
        if executable is None:
            return False
        try:
            result = subprocess.run(
                [executable, "version"],
                capture_output=True,
                text=True,
                timeout=self._config.connection_timeout_seconds,
                check=False,
            )
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    def list_devices(self) -> list[AdbDevice]:
        executable = shutil.which(self._config.adb_path)
        if executable is None:
            logger.warning("ADB not found at path: %s", self._config.adb_path)
            return []

        try:
            result = subprocess.run(
                [executable, "devices", "-l"],
                capture_output=True,
                text=True,
                timeout=self._config.connection_timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.error("Failed to list ADB devices: %s", exc)
            return []

        if result.returncode != 0:
            logger.error("ADB devices command failed: %s", result.stderr.strip())
            return []

        devices: list[AdbDevice] = []
        for line in result.stdout.splitlines()[1:]:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            serial, state = parts[0], parts[1]
            if state == "unauthorized":
                devices.append(AdbDevice(serial=serial, state=state))
                continue
            if state not in {"device", "offline"}:
                continue

            model = _extract_property(parts, "model:")
            product = _extract_property(parts, "product:")
            devices.append(
                AdbDevice(
                    serial=serial,
                    state=state,
                    model=model,
                    product=product,
                )
            )

        return devices

    def resolve_device_serial(self) -> str | None:
        if self._config.device_serial:
            return self._config.device_serial

        ready_devices = [device for device in self.list_devices() if device.state == "device"]
        if not ready_devices:
            return None
        if len(ready_devices) == 1:
            return ready_devices[0].serial

        logger.warning("Multiple devices connected, using the first one: %s", ready_devices[0].serial)
        return ready_devices[0].serial

    def capture_screenshot(self, output_path: Path, serial: str | None = None) -> Path:
        executable = shutil.which(self._config.adb_path)
        if executable is None:
            raise RuntimeError(f"ADB no encontrado en: {self._config.adb_path}")

        device_serial = serial or self.resolve_device_serial()
        if device_serial is None:
            raise RuntimeError("No hay ningún dispositivo listo para capturar.")

        command = [executable, "-s", device_serial, "exec-out", "screencap", "-p"]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                timeout=self._config.connection_timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError(f"Error al capturar pantalla: {exc}") from exc

        if result.returncode != 0:
            message = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(message or "ADB screencap falló.")

        if not result.stdout:
            raise RuntimeError("La captura de pantalla está vacía.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(result.stdout)
        logger.info("Screenshot saved to %s", output_path)
        return output_path


def _extract_property(parts: list[str], prefix: str) -> str | None:
    for part in parts:
        if part.startswith(prefix):
            return part.removeprefix(prefix).replace("_", " ")
    return None
