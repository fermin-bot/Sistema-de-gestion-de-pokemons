"""Motor OCR con PaddleOCR."""

from __future__ import annotations

from pathlib import Path

from config.schema import OcrConfig
from utils.logging import get_logger

logger = get_logger(__name__)


class OcrEngine:
    def __init__(self, config: OcrConfig) -> None:
        self._config = config
        self._engine = None

    def _ensure_loaded(self) -> None:
        if self._engine is not None:
            return

        from paddleocr import PaddleOCR

        logger.info("Loading PaddleOCR (language=%s)", self._config.language)
        self._engine = PaddleOCR(
            lang=self._config.language,
            use_gpu=self._config.use_gpu,
        )

    def extract_text(self, image_path: Path) -> str:
        self._ensure_loaded()
        assert self._engine is not None

        result = self._engine.predict(str(image_path))
        lines = _extract_lines(result)
        text = "\n".join(line for line in lines if line.strip())
        logger.info("OCR extracted %s lines from %s", len(lines), image_path)
        return text


def _extract_lines(result: object) -> list[str]:
    lines: list[str] = []

    if result is None:
        return lines

    if isinstance(result, str):
        return [result]

    if isinstance(result, dict):
        for key in ("rec_text", "text", "transcription"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                lines.append(value.strip())
        for value in result.values():
            lines.extend(_extract_lines(value))
        return _dedupe(lines)

    if isinstance(result, (list, tuple)):
        for item in result:
            lines.extend(_extract_lines(item))
        return _dedupe(lines)

    if hasattr(result, "text") and isinstance(result.text, str):
        lines.append(result.text.strip())

    return _dedupe(lines)


def _dedupe(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique.append(line)
    return unique
