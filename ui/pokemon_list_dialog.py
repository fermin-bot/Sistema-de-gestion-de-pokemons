"""Diálogo con la lista de Pokémon registrados."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from database.repository import PokemonRepository


class PokemonListDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk, pokemon_repo: PokemonRepository) -> None:
        super().__init__(parent)
        self._pokemon_repo = pokemon_repo

        self.title("Pokémon registrados")
        self.geometry("760x520")
        self.minsize(640, 400)
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_list()
        self._build_footer()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        count = self._pokemon_repo.count()
        ctk.CTkLabel(
            header,
            text=f"Pokémon registrados ({count})",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=8, pady=8)

    def _build_list(self) -> None:
        container = ctk.CTkFrame(self)
        container.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        headers = ctk.CTkFrame(container)
        headers.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        headers.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        for column, label in enumerate(("#", "Nombre", "CP", "IV", "Tipo", "Shiny", "Fecha")):
            ctk.CTkLabel(headers, text=label, font=ctk.CTkFont(weight="bold")).grid(
                row=0, column=column, sticky="w", padx=8, pady=4
            )

        scroll = ctk.CTkScrollableFrame(container)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        pokemon_list = self._pokemon_repo.list_all()
        if not pokemon_list:
            ctk.CTkLabel(
                scroll,
                text="Todavía no hay Pokémon guardados. Usa el escaneo automático.",
                anchor="w",
                justify="left",
                wraplength=680,
            ).grid(row=0, column=0, columnspan=7, sticky="w", padx=8, pady=16)
            return

        for row_index, pokemon in enumerate(pokemon_list, start=1):
            scanned_at = pokemon.scanned_at.strftime("%d/%m/%Y %H:%M") if pokemon.scanned_at else "-"
            if pokemon.primary_type and pokemon.secondary_type:
                pokemon_type = f"{pokemon.primary_type}/{pokemon.secondary_type}"
            elif pokemon.primary_type:
                pokemon_type = pokemon.primary_type
            else:
                pokemon_type = "-"
            values = (
                str(row_index),
                pokemon.name,
                str(pokemon.cp) if pokemon.cp is not None else "-",
                f"{pokemon.iv_percent:g}%" if pokemon.iv_percent is not None else "-",
                pokemon_type,
                "Sí" if pokemon.is_shiny else "No",
                scanned_at,
            )
            for column, value in enumerate(values):
                ctk.CTkLabel(scroll, text=value, anchor="w").grid(
                    row=row_index,
                    column=column,
                    sticky="w",
                    padx=8,
                    pady=4,
                )

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self)
        footer.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 16))

        ctk.CTkButton(footer, text="Vaciar lista", command=self._clear_all, fg_color="#8b1e1e").pack(
            side="left", padx=8, pady=8
        )
        ctk.CTkButton(footer, text="Cerrar", command=self.destroy).pack(side="right", padx=8, pady=8)

    def _clear_all(self) -> None:
        if not messagebox.askyesno(
            "Vaciar lista",
            "¿Seguro que quieres borrar todos los Pokémon guardados?",
        ):
            return
        self._pokemon_repo.clear_all()
        self.destroy()
