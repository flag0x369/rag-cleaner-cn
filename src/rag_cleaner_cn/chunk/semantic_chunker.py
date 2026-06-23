from __future__ import annotations

from rag_cleaner_cn.core.enums import (
    ChunkStatus,
    ChunkType,
    ContentValue,
    ParagraphType,
    SegmentAction,
    SourceType,
)
from rag_cleaner_cn.core.models import Chunk, CleanerConfig, Segment, SourceDocument
from rag_cleaner_cn.segment.heading import heading_level, heading_title, is_heading
from rag_cleaner_cn.utils.ids import chunk_id
from rag_cleaner_cn.utils.text import estimate_token_count


def build_chunks(
    document: SourceDocument,
    segments: list[Segment],
    config: CleanerConfig,
    drop_count: int = 0,
) -> list[Chunk]:
    """Build semantically coherent RAG chunks while preserving section context."""

    chunks: list[Chunk] = []
    section_stack: list[tuple[int, str]] = []
    pending: list[Segment] = []

    for segment in segments:
        if segment.action == SegmentAction.DROP:
            continue
        text = (segment.text_cleaned or "").strip()
        if not text:
            continue
        if segment.paragraph_type == ParagraphType.HEADING or is_heading(segment.text_original):
            _flush_pending(chunks, document, pending, section_stack, config, drop_count)
            pending = []
            level = heading_level(segment.text_original)
            title = heading_title(segment.text_original)
            section_stack = [
                (stack_level, value) for stack_level, value in section_stack if stack_level < level
            ]
            section_stack.append((level, title))
            continue
        pending.append(segment)
        if _pending_size(pending) >= config.chunking.target_chunk_size_chars:
            _flush_pending(chunks, document, pending, section_stack, config, drop_count)
            pending = []

    _flush_pending(chunks, document, pending, section_stack, config, drop_count)
    return chunks


def _flush_pending(
    chunks: list[Chunk],
    document: SourceDocument,
    pending: list[Segment],
    section_stack: list[tuple[int, str]],
    config: CleanerConfig,
    drop_count: int,
) -> None:
    if not pending:
        return
    section_path = [title for _, title in section_stack]
    paragraphs = [
        (segment.text_cleaned or "").strip() for segment in pending if segment.text_cleaned
    ]
    text_body = "\n\n".join(paragraphs).strip()
    if not text_body:
        return
    for part in _split_long_text(text_body, config.chunking.max_chunk_size_chars):
        chunk_text = _format_chunk_text(part, section_path, config)
        status = _chunk_status(part, pending, config)
        chunks.append(
            Chunk(
                chunk_id=chunk_id(document.doc_id, len(chunks) + 1),
                doc_id=document.doc_id,
                chunk_index=len(chunks) + 1,
                title=document.title,
                section_path=section_path,
                text=chunk_text,
                embedding_text_main=chunk_text,
                embedding_text_expanded=_expanded_text(document, chunk_text, config),
                source_type=document.source_type,
                source_url=document.source_url,
                source_file=document.source_file,
                page_start=_first_position_value(pending, "page"),
                page_end=_last_position_value(pending, "page"),
                start_time=_first_position_value(pending, "start_time"),
                end_time=_last_position_value(pending, "end_time"),
                speaker=_first_position_value(pending, "speaker"),
                chunk_status=status,
                chunk_type=_chunk_type(pending, document.source_type),
                quality_tags=sorted(
                    {tag for segment in pending for tag in segment.quality_tags}, key=str
                ),
                risk_tags=sorted(
                    {tag for segment in pending for tag in segment.risk_tags}, key=str
                ),
                repair_count=sum(segment.repair_count for segment in pending),
                drop_count=drop_count,
                token_estimate=estimate_token_count(chunk_text),
                metadata=_chunk_metadata(pending),
            )
        )


def _pending_size(pending: list[Segment]) -> int:
    return sum(len(segment.text_cleaned or "") for segment in pending)


def _split_long_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts: list[str] = []
    current = text
    while len(current) > max_chars:
        split_at = max(current.rfind("。", 0, max_chars), current.rfind("\n", 0, max_chars))
        if split_at <= 0:
            split_at = max_chars
        parts.append(current[: split_at + 1].strip())
        current = current[split_at + 1 :].strip()
    if current:
        parts.append(current)
    return parts


def _format_chunk_text(text: str, section_path: list[str], config: CleanerConfig) -> str:
    if config.chunking.add_section_path_to_text and section_path:
        return f"【{' > '.join(section_path)}】\n\n{text}"
    return text


def _expanded_text(document: SourceDocument, text: str, config: CleanerConfig) -> str | None:
    if not config.embedding.generate_expanded_text:
        return None
    title = document.title or ""
    return f"{title}\n\n{text}".strip()


def _chunk_status(
    text: str,
    pending: list[Segment],
    config: CleanerConfig,
) -> ChunkStatus:
    if any(segment.risk_tags or segment.action == SegmentAction.REVIEW for segment in pending):
        return ChunkStatus.REVIEW_CHUNK
    if len(text) < config.chunking.min_chunk_size_chars and any(
        segment.content_value in {ContentValue.HIGH, ContentValue.MEDIUM} for segment in pending
    ):
        return ChunkStatus.IMPORT_SHORT
    return ChunkStatus.IMPORT_CHUNK


def _chunk_type(pending: list[Segment], source_type: SourceType) -> ChunkType:
    paragraph_types = {segment.paragraph_type for segment in pending}
    if source_type in {SourceType.VIDEO_TRANSCRIPT, SourceType.AUDIO_TRANSCRIPT}:
        return ChunkType.TRANSCRIPT
    if paragraph_types & {
        ParagraphType.QUESTION,
        ParagraphType.ANSWER,
        ParagraphType.TRANSCRIPT_QUESTION,
    }:
        return ChunkType.QA
    if ParagraphType.STEP in paragraph_types:
        return ChunkType.STEP
    if ParagraphType.METHOD in paragraph_types:
        return ChunkType.METHOD
    if ParagraphType.CASE in paragraph_types:
        return ChunkType.CASE
    if ParagraphType.DEFINITION in paragraph_types:
        return ChunkType.DEFINITION
    if ParagraphType.BODY_CLAIM in paragraph_types:
        return ChunkType.CLAIM
    return ChunkType.MIXED


def _chunk_metadata(pending: list[Segment]) -> dict[str, list[str]]:
    metadata = {"segment_ids": [segment.segment_id for segment in pending]}
    review_reasons = sorted({segment.review_reason for segment in pending if segment.review_reason})
    if review_reasons:
        metadata["review_reasons"] = review_reasons
    return metadata


def _first_position_value(segments: list[Segment], key: str):
    for segment in segments:
        value = segment.source_position.get(key)
        if value is not None:
            return value
    return None


def _last_position_value(segments: list[Segment], key: str):
    for segment in reversed(segments):
        value = segment.source_position.get(key)
        if value is not None:
            return value
    return None
