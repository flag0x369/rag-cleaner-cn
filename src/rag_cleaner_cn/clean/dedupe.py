from __future__ import annotations


def mark_duplicates(texts: list[str]) -> set[int]:
    """Return indexes of exact duplicate paragraphs after the first occurrence."""

    seen: set[str] = set()
    duplicates: set[int] = set()
    for index, text in enumerate(texts):
        key = text.strip()
        if key in seen:
            duplicates.add(index)
        seen.add(key)
    return duplicates
