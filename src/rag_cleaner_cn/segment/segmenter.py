from __future__ import annotations

from typing import Any

from rag_cleaner_cn.core.enums import ParagraphType
from rag_cleaner_cn.core.models import Segment
from rag_cleaner_cn.normalize.speaker import split_speaker
from rag_cleaner_cn.normalize.whitespace import normalize_whitespace
from rag_cleaner_cn.segment.heading import is_heading
from rag_cleaner_cn.utils.ids import segment_id


def segment_text(
    text: str,
    doc_id: str,
    transcript_cues: list[dict[str, Any]] | None = None,
) -> list[Segment]:
    """Split normalized text or transcript cues into traceable segments."""

    if transcript_cues:
        return _segment_transcript(doc_id, transcript_cues)

    normalized = normalize_whitespace(text)
    if not normalized:
        return []

    blocks = [block.strip() for block in normalized.split("\n\n") if block.strip()]
    segments: list[Segment] = []
    index = 1
    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        for line in lines if any(is_heading(line) for line in lines) else [block]:
            speaker, speech = split_speaker(line)
            paragraph_type = ParagraphType.HEADING if is_heading(line) else ParagraphType.UNKNOWN
            if speaker:
                paragraph_type = ParagraphType.TRANSCRIPT_SPEECH
            segments.append(
                Segment(
                    segment_id=segment_id(doc_id, index),
                    doc_id=doc_id,
                    text_original=line,
                    text_normalized=speech,
                    paragraph_type=paragraph_type,
                    source_position={"speaker": speaker} if speaker else {},
                )
            )
            index += 1
    return segments


def _segment_transcript(doc_id: str, cues: list[dict[str, Any]]) -> list[Segment]:
    segments: list[Segment] = []
    for index, cue in enumerate(cues, start=1):
        text = str(cue.get("text", "")).strip()
        if not text:
            continue
        segments.append(
            Segment(
                segment_id=segment_id(doc_id, index),
                doc_id=doc_id,
                text_original=text,
                text_normalized=text,
                paragraph_type=ParagraphType.TRANSCRIPT_SPEECH,
                source_position={
                    "start_time": cue.get("start_time"),
                    "end_time": cue.get("end_time"),
                    "speaker": cue.get("speaker") or "speaker_unknown",
                },
            )
        )
    return segments
