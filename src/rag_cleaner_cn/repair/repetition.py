from __future__ import annotations

import re

_SAFE_STUTTER_PHRASES = {
    "我们",
    "你们",
    "他们",
    "大家",
    "今天",
    "这个",
    "那个",
    "问题",
    "增长",
}


def compress_repetition(text: str) -> tuple[str, bool]:
    """Compress obvious ASR/OCR stutters without removing rhetorical repetition."""

    original = text
    fixed = re.sub(r"([\u4e00-\u9fff]{2,4})\1", _compress_safe_stutter, text)
    fixed = re.sub(r"([^，。！？；]{2,20}[，,])\1", r"\1", fixed)
    return fixed, fixed != original


def _compress_safe_stutter(match: re.Match[str]) -> str:
    phrase = match.group(1)
    if phrase in _SAFE_STUTTER_PHRASES:
        return phrase
    return match.group(0)
