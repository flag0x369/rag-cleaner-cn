from __future__ import annotations

from collections import Counter


def repeated_short_lines(lines: list[str], min_repeats: int = 3) -> set[str]:
    """Return repeated short lines that are likely page headers or footers."""

    counter = Counter(line.strip() for line in lines if 0 < len(line.strip()) <= 30)
    return {line for line, count in counter.items() if count >= min_repeats}
