from __future__ import annotations

import re

_STEP_WORDS = "一二三四五六七八九十"


def restore_step_punctuation(text: str) -> tuple[str, bool]:
    """Restore punctuation for compact '第一步...第二步...' step transcripts."""

    original = text
    if len(re.findall(rf"第[{_STEP_WORDS}]步", text)) < 2:
        return text, False
    fixed = re.sub(rf"(第[{_STEP_WORDS}]步)", r"\n\1，", text)
    fixed = fixed.lstrip("\n")
    fixed = re.sub(rf"。?\n(第[{_STEP_WORDS}]步)", r"。\n\1", fixed)
    if not fixed.endswith(("。", "！", "？")):
        fixed = f"{fixed}。"
    return fixed, fixed != original
