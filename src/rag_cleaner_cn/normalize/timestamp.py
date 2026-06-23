from __future__ import annotations

import re

_SRT_TS_RE = re.compile(r"(?P<h>\d{1,2}):(?P<m>\d{2}):(?P<s>\d{2})(?P<ms>[,.]\d{1,3})?")


def normalize_timestamp(value: str) -> str | None:
    """Normalize SRT/VTT timestamps to HH:MM:SS.mmm."""

    match = _SRT_TS_RE.search(value.strip())
    if not match:
        return None
    ms = (match.group("ms") or ".000").replace(",", ".")
    ms = f"{ms:<04}"[:4]
    return (
        f"{int(match.group('h')):02d}:{int(match.group('m')):02d}:{int(match.group('s')):02d}{ms}"
    )


def is_timestamp_only(text: str) -> bool:
    stripped = text.strip()
    return bool(_SRT_TS_RE.fullmatch(stripped) or "-->" in stripped and len(stripped) < 40)
