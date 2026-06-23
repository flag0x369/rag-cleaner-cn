from __future__ import annotations

import re

_SPEAKER_RE = re.compile(r"^(?P<speaker>[\u4e00-\u9fffA-Za-z0-9_ -]{1,16})[：:]\s*(?P<text>.+)$")


def split_speaker(text: str) -> tuple[str | None, str]:
    """Split a leading speaker label such as '讲师：内容'."""

    match = _SPEAKER_RE.match(text.strip())
    if not match:
        return None, text
    return match.group("speaker").strip(), match.group("text").strip()
