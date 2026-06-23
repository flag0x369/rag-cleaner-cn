from __future__ import annotations

import re
from typing import Any

from rag_cleaner_cn.normalize.speaker import split_speaker
from rag_cleaner_cn.normalize.timestamp import normalize_timestamp

_TIME_RANGE_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*"
    r"(?P<end>\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})"
)


def parse_transcript_blocks(raw_text: str) -> list[dict[str, Any]]:
    """Parse simple SRT/VTT blocks into cue dictionaries."""

    text = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    text = re.sub(r"^WEBVTT\s*", "", text, flags=re.IGNORECASE).strip()
    blocks = re.split(r"\n{2,}", text)
    cues: list[dict[str, Any]] = []
    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        if re.fullmatch(r"\d+", lines[0]):
            lines = lines[1:]
        if not lines:
            continue
        match = _TIME_RANGE_RE.search(lines[0])
        if not match:
            continue
        cue_text = " ".join(lines[1:]).strip()
        if not cue_text:
            continue
        speaker, clean_text = split_speaker(cue_text)
        cues.append(
            {
                "start_time": normalize_timestamp(match.group("start")),
                "end_time": normalize_timestamp(match.group("end")),
                "speaker": speaker or "speaker_unknown",
                "text": clean_text,
            }
        )
    return cues
