"""Escaneo automático de la caja Pokémon."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from adb import AdbClient
from config.schema import ScanConfig
from database.repository import PokemonRepository
from models.pokemon import Pokemon
from ocr import OcrEngine
from rules.parser import ParsedPokemon, parse_pokemon_ocr
from scanner.test_scan import build_screenshot_path, capture_screenshot
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class BoxScanProgress:
    index: int
    scanned_count: int
    skipped_count: int
    current_name: str
    message: str
    screenshot_path: Path | None
    ocr_text: str
    running: bool


@dataclass(slots=True)
class BoxScanResult:
    scanned_count: int
    skipped_count: int
    stopped_reason: str


class BoxScanner:
    def __init__(
        self,
        adb_client: AdbClient,
        ocr_engine: OcrEngine,
        pokemon_repo: PokemonRepository,
        scan_config: ScanConfig,
    ) -> None:
        self._adb_client = adb_client
        self._ocr_engine = ocr_engine
        self._pokemon_repo = pokemon_repo
        self._config = scan_config
        self._stop_requested = False

    def request_stop(self) -> None:
        self._stop_requested = True

    def run(self, on_progress: Callable[[BoxScanProgress], None] | None = None) -> BoxScanResult:
        self._stop_requested = False
        device_serial = self._adb_client.resolve_device_serial()
        if device_serial is None:
            raise RuntimeError("No hay ningún dispositivo Android listo.")

        scanned_count = 0
        skipped_count = 0
        first_fingerprint: str | None = None
        stopped_reason = "Completado"

        for index in range(self._config.max_scroll_attempts):
            if self._stop_requested:
                stopped_reason = "Detenido por el usuario"
                break

            screenshot_path, _ = capture_screenshot(self._adb_client, self._config)
            ocr_text = self._ocr_engine.extract_text(screenshot_path)
            parsed = parse_pokemon_ocr(ocr_text)

            if parsed is None:
                skipped_count += 1
                message = f"No se pudo leer el Pokémon #{index + 1}"
                self._emit_progress(
                    on_progress,
                    BoxScanProgress(
                        index=index + 1,
                        scanned_count=scanned_count,
                        skipped_count=skipped_count,
                        current_name="?",
                        message=message,
                        screenshot_path=screenshot_path,
                        ocr_text=ocr_text,
                        running=True,
                    ),
                )
            else:
                if not parsed.is_valid:
                    skipped_count += 1
                    message = f"Pokémon #{index + 1} no válido, omitido"
                    self._emit_progress(
                        on_progress,
                        BoxScanProgress(
                            index=index + 1,
                            scanned_count=scanned_count,
                            skipped_count=skipped_count,
                            current_name="?",
                            message=message,
                            screenshot_path=screenshot_path,
                            ocr_text=ocr_text,
                            running=True,
                        ),
                    )
                    if index + 1 >= self._config.max_scroll_attempts:
                        stopped_reason = "Límite de intentos alcanzado"
                        break
                    if self._stop_requested:
                        stopped_reason = "Detenido por el usuario"
                        break
                    self._adb_client.swipe_to_next_pokemon(
                        duration_ms=self._config.swipe_duration_ms,
                        serial=device_serial,
                    )
                    time.sleep(self._config.delay_between_pokemon_ms / 1000)
                    continue

                fingerprint = parsed.fingerprint
                if self._config.stop_on_duplicate:
                    if index == 0:
                        first_fingerprint = fingerprint
                    elif first_fingerprint and fingerprint == first_fingerprint:
                        stopped_reason = "Fin de la caja detectado"
                        break

                self._save_pokemon(parsed, device_serial)
                scanned_count += 1
                message = f"Guardado: {parsed.name}" + (f" (CP {parsed.cp})" if parsed.cp else "")
                self._emit_progress(
                    on_progress,
                    BoxScanProgress(
                        index=index + 1,
                        scanned_count=scanned_count,
                        skipped_count=skipped_count,
                        current_name=parsed.name,
                        message=message,
                        screenshot_path=screenshot_path,
                        ocr_text=ocr_text,
                        running=True,
                    ),
                )

            if index + 1 >= self._config.max_scroll_attempts:
                stopped_reason = "Límite de intentos alcanzado"
                break

            if self._stop_requested:
                stopped_reason = "Detenido por el usuario"
                break

            self._adb_client.swipe_to_next_pokemon(
                duration_ms=self._config.swipe_duration_ms,
                serial=device_serial,
            )
            time.sleep(self._config.delay_between_pokemon_ms / 1000)

        self._emit_progress(
            on_progress,
            BoxScanProgress(
                index=scanned_count + skipped_count,
                scanned_count=scanned_count,
                skipped_count=skipped_count,
                current_name="",
                message=stopped_reason,
                screenshot_path=None,
                ocr_text="",
                running=False,
            ),
        )

        return BoxScanResult(
            scanned_count=scanned_count,
            skipped_count=skipped_count,
            stopped_reason=stopped_reason,
        )

    def _save_pokemon(self, parsed: ParsedPokemon, device_serial: str) -> None:
        pokemon = Pokemon(
            name=parsed.name,
            cp=parsed.cp,
            iv_percent=parsed.iv_percent,
            primary_type=parsed.primary_type,
            secondary_type=parsed.secondary_type,
            is_shiny=parsed.is_shiny,
            device_serial=device_serial,
            raw_ocr_text=parsed.raw_ocr_text,
        )
        self._pokemon_repo.add(pokemon)
        logger.info("Saved pokemon %s (CP=%s)", parsed.name, parsed.cp)

    @staticmethod
    def _emit_progress(
        callback: Callable[[BoxScanProgress], None] | None,
        progress: BoxScanProgress,
    ) -> None:
        if callback is not None:
            callback(progress)
