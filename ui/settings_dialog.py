"""Diálogo de ajustes de la aplicación."""

from __future__ import annotations

import customtkinter as ctk

from config.manager import ConfigManager
from config.schema import AppConfig


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk, config_manager: ConfigManager) -> None:
        super().__init__(parent)
        self._config_manager = config_manager
        self._config = config_manager.config

        self.title("Ajustes")
        self.geometry("520x560")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        self._adb_path = ctk.StringVar(value=self._config.adb.adb_path)
        self._scrcpy_path = ctk.StringVar(value=self._config.adb.scrcpy_path)
        self._device_serial = ctk.StringVar(value=self._config.adb.device_serial or "")
        self._ocr_language = ctk.StringVar(value=self._config.ocr.language)
        self._scan_delay = ctk.StringVar(value=str(self._config.scan.delay_between_pokemon_ms))
        self._appearance_mode = ctk.StringVar(value=self._config.ui.appearance_mode)

        self._build_form()
        self._build_actions()

    def _build_form(self) -> None:
        form = ctk.CTkScrollableFrame(self)
        form.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        form.grid_columnconfigure(0, weight=1)

        fields = (
            ("Ruta ADB", self._adb_path),
            ("Ruta scrcpy", self._scrcpy_path),
            ("Serial del dispositivo (opcional)", self._device_serial),
            ("Idioma OCR", self._ocr_language),
            ("Delay entre Pokémon (ms)", self._scan_delay),
        )
        for row, (label, variable) in enumerate(fields):
            ctk.CTkLabel(form, text=label, anchor="w").grid(
                row=row * 2,
                column=0,
                sticky="ew",
                pady=(8, 0),
            )
            ctk.CTkEntry(form, textvariable=variable).grid(
                row=row * 2 + 1,
                column=0,
                sticky="ew",
                pady=(0, 4),
            )

        appearance_row = len(fields) * 2
        ctk.CTkLabel(form, text="Modo visual", anchor="w").grid(
            row=appearance_row,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )
        ctk.CTkOptionMenu(
            form,
            variable=self._appearance_mode,
            values=["dark", "light", "system"],
        ).grid(row=appearance_row + 1, column=0, sticky="ew", pady=(0, 4))

    def _build_actions(self) -> None:
        actions = ctk.CTkFrame(self)
        actions.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))

        ctk.CTkButton(actions, text="Guardar", command=self._save).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Cancelar", command=self.destroy).pack(side="left")

    def _save(self) -> None:
        try:
            delay = int(self._scan_delay.get().strip())
        except ValueError:
            delay = self._config.scan.delay_between_pokemon_ms

        device_serial = self._device_serial.get().strip() or None
        updated = AppConfig(
            log_level=self._config.log_level,
            database_filename=self._config.database_filename,
            adb=self._config.adb.__class__(
                adb_path=self._adb_path.get().strip() or "adb",
                scrcpy_path=self._scrcpy_path.get().strip() or "scrcpy",
                device_serial=device_serial,
                connection_timeout_seconds=self._config.adb.connection_timeout_seconds,
            ),
            ocr=self._config.ocr.__class__(
                language=self._ocr_language.get().strip() or "en",
                use_gpu=self._config.ocr.use_gpu,
                confidence_threshold=self._config.ocr.confidence_threshold,
            ),
            scan=self._config.scan.__class__(
                delay_between_pokemon_ms=delay,
                screenshot_format=self._config.scan.screenshot_format,
                max_scroll_attempts=self._config.scan.max_scroll_attempts,
            ),
            ui=self._config.ui.__class__(
                theme=self._config.ui.theme,
                appearance_mode=self._appearance_mode.get(),
                color_theme=self._config.ui.color_theme,
                window_width=self._config.ui.window_width,
                window_height=self._config.ui.window_height,
            ),
        )
        self._config_manager.update(updated)
        self._config = updated
        self.destroy()
