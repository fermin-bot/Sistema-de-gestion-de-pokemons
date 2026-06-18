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

        import warnings

        try:
            from requests import RequestsDependencyWarning

            warnings.filterwarnings("ignore", category=RequestsDependencyWarning)
        except ImportError:
            pass

        from paddleocr import PaddleOCR

        logger.info("Loading PaddleOCR (language=%s)", self._config.language)

        init_kwargs: dict[str, object] = {
            # Evita fallos de oneDNN en Windows con Paddle 3.x.
            "enable_mkldnn": False,
            # Capturas de móvil: no hace falta preprocesado de documento.
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
        }
        if self._config.use_gpu:
            init_kwargs["device"] = "gpu"

        self._engine = PaddleOCR(
            lang=self._config.language,
            **init_kwargs,
        )

    def extract_text(self, image_path: Path) -> str:
        self._ensure_loaded()
        assert self._engine is not None

        result = list(self._engine.predict(str(image_path)))
        lines = _extract_lines(result, self._config.confidence_threshold)
        text = "\n".join(line for line in lines if line.strip())
        logger.info("OCR extracted %s lines from %s", len(lines), image_path)
        return text


def _extract_lines(result: object, confidence_threshold: float) -> list[str]:
    lines: list[str] = []

    if result is None:
        return lines

    if isinstance(result, str):
        return [result]

    if isinstance(result, dict):
        rec_texts = result.get("rec_texts")
        rec_scores = result.get("rec_scores")
        if isinstance(rec_texts, list):
            for index, text in enumerate(rec_texts):
                if not isinstance(text, str) or not text.strip():
                    continue
                if isinstance(rec_scores, list) and index < len(rec_scores):
                    score = rec_scores[index]
                    if isinstance(score, (int, float)) and score < confidence_threshold:
                        continue
                lines.append(text.strip())
            return _dedupe(lines)

        for key in ("rec_text", "text", "transcription"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                lines.append(value.strip())

        for value in result.values():
            if isinstance(value, (str, int, float, bool)):
                continue
            lines.extend(_extract_lines(value, confidence_threshold))
        return _dedupe(lines)

    if isinstance(result, (list, tuple)):
        for item in result:
            lines.extend(_extract_lines(item, confidence_threshold))
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
