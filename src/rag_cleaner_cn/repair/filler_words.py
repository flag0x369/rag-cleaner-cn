from __future__ import annotations

import re


def remove_filler_words(text: str, filler_words: list[str]) -> tuple[str, bool]:
    """Remove filler words only when they are standalone discourse fillers."""

    original = text
    fixed = text
    fixed = re.sub(
        r"^哈喽大家好[啊呀，,\s]*我是[\u4e00-\u9fffA-Za-z]{1,6}?[啊呀，,\s]+",
        "",
        fixed,
    )
    fixed = _remove_oral_particles(fixed)
    fixed = _remove_oral_discourse_phrases(fixed)
    for word in sorted(filler_words, key=len, reverse=True):
        fixed = re.sub(rf"(^|[，,。\s]){re.escape(word)}([，,。\s]|$)", r"\1", fixed)
    fixed = re.sub(r"^嗯[，,\s]*", "", fixed)
    fixed = re.sub(r"(?<=今天)呢(?=[，,])", "", fixed)
    fixed = re.sub(r"其实呢", "其实", fixed)
    fixed = re.sub(r"\s{2,}", " ", fixed)
    fixed = re.sub(r"[，,]\s*[，,]", "，", fixed)
    fixed = re.sub(r"^[，,]\s*", "", fixed.strip())
    if not fixed:
        return original, False
    return fixed, fixed != original


def _remove_oral_particles(text: str) -> str:
    fixed = text
    for particle in ("呃", "嗯", "额", "啊"):
        fixed = fixed.replace(particle, "")
    return fixed


def _remove_oral_discourse_phrases(text: str) -> str:
    fixed = text
    for phrase in ("然后呢", "这个呢", "那个呢", "就是说", "怎么说呢"):
        fixed = re.sub(rf"{re.escape(phrase)}(?![？?])", "", fixed)
    for phrase in ("对吧", "对不对", "好不好", "好吧", "清楚吗"):
        fixed = fixed.replace(phrase, "")
    return fixed
