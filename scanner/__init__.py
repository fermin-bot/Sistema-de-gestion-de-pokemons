"""Orquestación del escaneo de la caja."""

from scanner.box_scanner import BoxScanProgress, BoxScanResult, BoxScanner
from scanner.test_scan import TestScanResult, capture_screenshot, run_test_scan

__all__ = [
    "BoxScanProgress",
    "BoxScanResult",
    "BoxScanner",
    "TestScanResult",
    "capture_screenshot",
    "run_test_scan",
]
