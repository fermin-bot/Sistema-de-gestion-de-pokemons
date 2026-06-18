"""Reglas para interpretar texto OCR de Pokémon GO."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True)
class ParsedPokemon:
    name: str
    cp: int | None = None
    iv_percent: float | None = None
    primary_type: str | None = None
    secondary_type: str | None = None
    is_shiny: bool = False
    raw_ocr_text: str = ""

    @property
    def fingerprint(self) -> str:
        return f"{self.name.lower()}|{self.cp or 0}"

    @property
    def is_valid(self) -> bool:
        return self.name not in {"", "Desconocido"} and _is_valid_name(self.name)


_CP_PATTERN = re.compile(r"(?:CP|PC|Pc)\s*[:#]?\s*(\d{2,4})\b", re.IGNORECASE)
_CP_SUFFIX_PATTERN = re.compile(r"(\d{2,4})\s*(?:CP|PC)\b", re.IGNORECASE)
_HP_PATTERN = re.compile(r"(\d+)\s*/\s*(\d+)\s*PS", re.IGNORECASE)
_IV_PATTERN = re.compile(r"(\d{1,3})\s*%")
_SHINY_PATTERN = re.compile(r"\b(shiny|variocolor)\b", re.IGNORECASE)
_TYPE_PATTERN = re.compile(
    r"\b(PLANTA|VENENO|FUEGO|AGUA|ELÉCTRICO|ELECTRICO|HIELO|LUCHA|VENENO|"
    r"TIERRA|VOLADOR|PSÍQUICO|PSIQUICO|BICHO|ROCA|FANTASMA|DRAGÓN|DRAGON|"
    r"SINIESTRO|ACERO|HADA|NORMAL)\b",
    re.IGNORECASE,
)
_NOISE_LINE_PATTERN = re.compile(
    r"^(?:\d{1,2}:\d{2}|NOO|NQO|NO|5G|KB/s|\d+[,.]?\d*\s*(?:KB/s|5G)?|"
    r"POLVOS|CARAMELOS|ESTELARES|EVOLUCIONAR|GIMNASIOS|INCURSIONES|ENTRENADOR|"
    r"MEGAENERGÍA|MEGAEVOLUCIONAR|MÁS PODER|PESO|ALTURA|antiguos|"
    r"power up|favorite|appraise|transfer|buddy|mega|lucky|weather|nivel|level|"
    r"pasarela|acceso peatonal|golmayo|burgos|camaretas).*$",
    re.IGNORECASE,
)
_UI_WORDS = {
    "noo",
    "nqo",
    "antiguos",
    "evolucionar",
    "entrenador",
    "polvos",
    "caramelos",
    "estelares",
    "peso",
    "altura",
    "gimnasios",
    "incursiones",
    "combates",
    "ascuas",
    "placaje",
    "más",
    "poder",
    "megaenergía",
    "megaevolucionar",
    "pasarela",
    "golmayo",
    "camaretas",
    "burgos",
    "soria",
}


def parse_pokemon_ocr(text: str) -> ParsedPokemon | None:
    if not _HP_PATTERN.search(text):
        return None

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None

    cp = _extract_cp(lines)
    iv_percent = _extract_iv(lines)
    is_shiny = any(_SHINY_PATTERN.search(line) for line in lines)
    primary_type, secondary_type = _extract_types(lines)
    name = _guess_name(lines)

    if name is None:
        return None

    return ParsedPokemon(
        name=name,
        cp=cp,
        iv_percent=iv_percent,
        primary_type=primary_type,
        secondary_type=secondary_type,
        is_shiny=is_shiny,
        raw_ocr_text=text,
    )


def _extract_cp(lines: list[str]) -> int | None:
    for line in lines:
        if _HP_PATTERN.search(line):
            continue
        match = _CP_PATTERN.search(line) or _CP_SUFFIX_PATTERN.search(line)
        if match:
            value = int(match.group(1))
            if 10 <= value <= 9999:
                return value
    return None


def _extract_iv(lines: list[str]) -> float | None:
    for line in lines:
        match = _IV_PATTERN.search(line)
        if match:
            value = float(match.group(1))
            if 0 < value <= 100:
                return value
    return None


def _extract_types(lines: list[str]) -> tuple[str | None, str | None]:
    for line in lines:
        if "/" in line:
            parts = [part.strip() for part in line.split("/") if part.strip()]
            types = [part for part in parts if _TYPE_PATTERN.fullmatch(part)]
            if types:
                primary = types[0].title()
                secondary = types[1].title() if len(types) > 1 else None
                return primary, secondary

        match = _TYPE_PATTERN.fullmatch(line)
        if match:
            return match.group(1).title(), None

    return None, None


def _guess_name(lines: list[str]) -> str | None:
    for index, line in enumerate(lines):
        if index + 1 < len(lines) and _HP_PATTERN.search(lines[index + 1]):
            if _is_valid_name(line):
                return _normalize_name(line)

    title_case_candidates = [
        line for line in lines if _is_valid_name(line) and not line.isupper() and " / " not in line
    ]
    if title_case_candidates:
        return _normalize_name(title_case_candidates[0])

    uppercase_candidates = [
        line
        for line in lines
        if _is_valid_name(line) and line.isupper() and len(line) >= 4 and " / " not in line
    ]
    if uppercase_candidates:
        return _normalize_name(uppercase_candidates[0])

    return None


def _is_valid_name(line: str) -> bool:
    cleaned = line.strip()
    if len(cleaned) < 3:
        return False
    if _NOISE_LINE_PATTERN.match(cleaned):
        return False
    if _CP_PATTERN.search(cleaned) or _CP_SUFFIX_PATTERN.search(cleaned):
        return False
    if _HP_PATTERN.search(cleaned):
        return False
    if re.fullmatch(r"[\d\W]+", cleaned):
        return False
    if cleaned.lower() in _UI_WORDS:
        return False
    if re.search(r"\d", cleaned) and not re.search(r"[A-Za-zÀ-ÿ]{3,}", cleaned):
        return False
    return bool(re.search(r"[A-Za-zÀ-ÿ]", cleaned))


def _normalize_name(name: str) -> str:
    if name.isupper():
        return name.title()
    return name.strip()
