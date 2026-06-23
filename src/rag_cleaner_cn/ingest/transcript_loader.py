from __future__ import annotations

from pathlib import Path

from rag_cleaner_cn.core.enums import SourceType
from rag_cleaner_cn.core.models import SourceDocument
from rag_cleaner_cn.ingest.base import build_source_document
from rag_cleaner_cn.segment.transcript import parse_transcript_blocks


class TranscriptLoader:
    supported_suffixes = {".srt", ".vtt"}

    def load(self, path: Path, source_type: SourceType | None = None) -> SourceDocument:
        raw = path.read_text(encoding="utf-8")
        cues = parse_transcript_blocks(raw)
        text = "\n\n".join(cue["text"] for cue in cues) if cues else raw
        return build_source_document(
            text,
            path=path,
            source_type=source_type or SourceType.VIDEO_TRANSCRIPT,
            metadata={"transcript_cues": cues},
        )
