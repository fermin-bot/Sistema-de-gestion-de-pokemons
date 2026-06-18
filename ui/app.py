"""Ventana principal de la aplicación."""

from __future__ import annotations

import threading
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from adb import AdbClient
from config.manager import ConfigManager
from core.constants import APP_NAME, APP_VERSION
from database import PokemonRepository, count_pokemon
from ocr import OcrEngine
from scanner import capture_screenshot, run_test_scan
from ui.settings_dialog import SettingsDialog
from utils.paths import get_config_path, get_database_path, get_exports_dir, get_logs_dir, get_screenshots_dir


class MainWindow(ctk.CTk):
    """Ventana principal con estado básico de la aplicación."""

    def __init__(self, config_manager: ConfigManager) -> None:
        super().__init__()
        self._config_manager = config_manager
        self._config = config_manager.config
        self._adb_client = AdbClient(self._config.adb)
        self._ocr_engine = OcrEngine(self._config.ocr)
        self._pokemon_repo = PokemonRepository()
        self._preview_image: ctk.CTkImage | None = None
        self._busy = False

        self._status_var = ctk.StringVar(value="Base iniciada correctamente")
        self._adb_status_var = ctk.StringVar(value="ADB: comprobando...")
        self._device_list_var = ctk.StringVar(value="Sin dispositivos detectados")
        self._pokemon_count_var = ctk.StringVar(value=f"Pokémon en base de datos: {count_pokemon()}")
        self._capture_path_var = ctk.StringVar(value="Sin capturas todavía")

        ctk.set_appearance_mode(self._config.ui.appearance_mode)
        ctk.set_default_color_theme(self._config.ui.color_theme)

        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry(f"{self._config.ui.window_width}x{self._config.ui.window_height}")
        self.minsize(960, 720)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_content()
        self._build_scan_panel()
        self._build_footer()
        self.after(200, self._refresh_device_status)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=APP_NAME,
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            header,
            text="Captura de pantalla por ADB y escaneo de prueba con OCR ya disponibles.",
            anchor="w",
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 16))

    def _build_content(self) -> None:
        content = ctk.CTkFrame(self)
        content.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        content.grid_columnconfigure((0, 1), weight=1)
        content.grid_rowconfigure((0, 1), weight=1)

        self._build_status_panel(content)
        self._build_device_panel(content)
        self._build_database_panel(content)
        self._build_actions_panel(content)

    def _build_status_panel(self, parent: ctk.CTkFrame) -> None:
        panel = ctk.CTkFrame(parent)
        panel.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=(16, 8))

        ctk.CTkLabel(panel, text="Estado", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", padx=16, pady=(16, 8)
        )

        for text in (
            "Aplicación arrancada",
            "Base de datos inicializada",
            "Captura ADB disponible",
            "OCR de prueba disponible",
        ):
            ctk.CTkLabel(panel, text=f"- {text}", anchor="w").pack(fill="x", padx=16, pady=4)

        ctk.CTkLabel(panel, textvariable=self._pokemon_count_var, anchor="w").pack(
            fill="x", padx=16, pady=(12, 16)
        )

    def _build_device_panel(self, parent: ctk.CTkFrame) -> None:
        panel = ctk.CTkFrame(parent)
        panel.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=(16, 8))

        ctk.CTkLabel(panel, text="Dispositivo Android", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", padx=16, pady=(16, 8)
        )

        ctk.CTkLabel(panel, textvariable=self._adb_status_var, anchor="w").pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(
            panel,
            textvariable=self._device_list_var,
            anchor="w",
            justify="left",
            wraplength=420,
        ).pack(fill="x", padx=16, pady=(4, 12))

        ctk.CTkButton(panel, text="Buscar dispositivos", command=self._refresh_device_status).pack(
            anchor="w", padx=16, pady=(0, 16)
        )

    def _build_database_panel(self, parent: ctk.CTkFrame) -> None:
        panel = ctk.CTkFrame(parent)
        panel.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=(8, 16))

        ctk.CTkLabel(panel, text="Rutas", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", padx=16, pady=(16, 8)
        )

        rows = (
            ("Config", str(get_config_path())),
            ("Base de datos", str(get_database_path())),
            ("Capturas", str(get_screenshots_dir())),
            ("Logs", str(get_logs_dir())),
            ("Exports", str(get_exports_dir())),
        )
        for label, value in rows:
            ctk.CTkLabel(panel, text=label, font=ctk.CTkFont(weight="bold")).pack(
                anchor="w", padx=16, pady=(8, 0)
            )
            ctk.CTkLabel(panel, text=value, anchor="w", justify="left", wraplength=420).pack(
                fill="x", padx=16, pady=(0, 4)
            )

    def _build_actions_panel(self, parent: ctk.CTkFrame) -> None:
        panel = ctk.CTkFrame(parent)
        panel.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=(8, 16))

        ctk.CTkLabel(panel, text="Acciones", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", padx=16, pady=(16, 8)
        )

        ctk.CTkLabel(
            panel,
            text=(
                "Abre Pokémon GO en el móvil, conéctalo por USB y usa captura o escaneo de prueba. "
                "La primera vez el OCR puede tardar porque descarga modelos."
            ),
            anchor="w",
            justify="left",
            wraplength=420,
        ).pack(fill="x", padx=16, pady=(0, 12))

        self._capture_button = ctk.CTkButton(panel, text="Capturar pantalla", command=self._start_capture)
        self._capture_button.pack(anchor="w", padx=16, pady=(0, 8))

        self._scan_button = ctk.CTkButton(panel, text="Escaneo de prueba", command=self._start_test_scan)
        self._scan_button.pack(anchor="w", padx=16, pady=(0, 8))

        ctk.CTkButton(panel, text="Comprobar estado", command=self._check_status).pack(
            anchor="w", padx=16, pady=(0, 8)
        )
        ctk.CTkButton(panel, text="Ajustes", command=self._open_settings).pack(anchor="w", padx=16, pady=(0, 8))
        ctk.CTkButton(panel, text="Cerrar", command=self.destroy).pack(anchor="w", padx=16, pady=(0, 16))

    def _build_scan_panel(self) -> None:
        panel = ctk.CTkFrame(self)
        panel.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 8))
        panel.grid_columnconfigure((0, 1), weight=1)
        panel.grid_rowconfigure(0, weight=1)

        preview_panel = ctk.CTkFrame(panel)
        preview_panel.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        preview_panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(preview_panel, text="Última captura", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 8)
        )
        self._preview_label = ctk.CTkLabel(
            preview_panel,
            text="Todavía no hay captura",
            width=320,
            height=480,
        )
        self._preview_label.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        ctk.CTkLabel(preview_panel, textvariable=self._capture_path_var, anchor="w", justify="left", wraplength=360).grid(
            row=2, column=0, sticky="ew", padx=16, pady=(0, 16)
        )

        ocr_panel = ctk.CTkFrame(panel)
        ocr_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        ocr_panel.grid_rowconfigure(1, weight=1)
        ocr_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(ocr_panel, text="Texto detectado (OCR)", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 8)
        )
        self._ocr_textbox = ctk.CTkTextbox(ocr_panel, height=480)
        self._ocr_textbox.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self._ocr_textbox.insert("1.0", "El texto OCR aparecerá aquí tras un escaneo de prueba.")

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self)
        footer.grid(row=3, column=0, sticky="ew", padx=16, pady=(8, 16))
        ctk.CTkLabel(footer, textvariable=self._status_var, anchor="w").pack(fill="x", padx=16, pady=12)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        self._capture_button.configure(state=state)
        self._scan_button.configure(state=state)

    def _reload_services(self) -> None:
        self._config = self._config_manager.config
        self._adb_client = AdbClient(self._config.adb)
        self._ocr_engine = OcrEngine(self._config.ocr)

    def _refresh_device_status(self) -> None:
        self._reload_services()

        if not self._adb_client.is_available():
            self._adb_status_var.set(f"ADB no encontrado en: {self._config.adb.adb_path}")
            self._device_list_var.set("Instala Android Platform Tools o indica la ruta en Ajustes.")
            self._status_var.set("ADB no disponible.")
            return

        devices = self._adb_client.list_devices()
        if not devices:
            self._adb_status_var.set("ADB disponible")
            self._device_list_var.set("No hay dispositivos conectados.")
            self._status_var.set("ADB listo, pero no se detectó ningún dispositivo.")
            return

        lines = []
        for device in devices:
            label = device.model or device.product or device.serial
            lines.append(f"- {label} ({device.serial}) [{device.state}]")

        self._adb_status_var.set(f"ADB disponible · {len(devices)} dispositivo(s)")
        self._device_list_var.set("\n".join(lines))
        self._status_var.set("Dispositivos detectados correctamente.")

    def _start_capture(self) -> None:
        if self._busy:
            return
        self._set_busy(True)
        self._status_var.set("Capturando pantalla...")
        threading.Thread(target=self._capture_worker, daemon=True).start()

    def _capture_worker(self) -> None:
        try:
            self._reload_services()
            screenshot_path, device_serial = capture_screenshot(self._adb_client, self._config.scan)
            message = f"Captura guardada desde {device_serial}."
            self.after(0, lambda: self._on_capture_success(screenshot_path, message, ""))
        except Exception as exc:
            self.after(0, lambda: self._on_task_error(str(exc)))

    def _start_test_scan(self) -> None:
        if self._busy:
            return
        self._set_busy(True)
        self._status_var.set("Ejecutando escaneo de prueba (puede tardar la primera vez)...")
        threading.Thread(target=self._test_scan_worker, daemon=True).start()

    def _test_scan_worker(self) -> None:
        try:
            self._reload_services()
            result = run_test_scan(self._adb_client, self._ocr_engine, self._config.scan)
            self.after(
                0,
                lambda: self._on_capture_success(result.screenshot_path, result.message, result.ocr_text),
            )
        except Exception as exc:
            self.after(0, lambda: self._on_task_error(str(exc)))

    def _on_capture_success(self, screenshot_path: Path, message: str, ocr_text: str) -> None:
        self._set_busy(False)
        self._capture_path_var.set(str(screenshot_path))
        self._status_var.set(message)
        self._show_preview(screenshot_path)
        if ocr_text:
            self._set_ocr_text(ocr_text)

    def _on_task_error(self, message: str) -> None:
        self._set_busy(False)
        self._status_var.set(message)

    def _show_preview(self, screenshot_path: Path) -> None:
        image = Image.open(screenshot_path)
        image.thumbnail((320, 480))
        self._preview_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
        self._preview_label.configure(image=self._preview_image, text="")

    def _set_ocr_text(self, text: str) -> None:
        self._ocr_textbox.delete("1.0", "end")
        self._ocr_textbox.insert("1.0", text)

    def _check_status(self) -> None:
        pokemon_count = self._pokemon_repo.count()
        self._pokemon_count_var.set(f"Pokémon en base de datos: {pokemon_count}")
        self._refresh_device_status()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self, self._config_manager)
        self.wait_window(dialog)
        self._reload_services()
        ctk.set_appearance_mode(self._config.ui.appearance_mode)
        self._status_var.set("Ajustes guardados.")


def run_app(config_manager: ConfigManager) -> int:
    """Arranca la ventana principal."""
    window = MainWindow(config_manager)
    window.mainloop()
    return 0
