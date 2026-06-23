from __future__ import annotations


def apply_ocr_rules(text: str) -> tuple[str, bool]:
    """Apply built-in high-confidence OCR character fixes.

    v0.1 ships no unconditional character replacements because Chinese OCR
    confusions are context-sensitive. Keep this hook disabled by default until a
    real rule is backed by tests and repair-log expectations.
    """

    return text, False
