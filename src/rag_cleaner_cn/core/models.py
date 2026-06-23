from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from rag_cleaner_cn.core.enums import (
    ChunkStatus,
    ChunkType,
    Confidence,
    ContentValue,
    DocumentStatus,
    NoiseType,
    ParagraphType,
    QualityTag,
    RepairType,
    RiskTag,
    SegmentAction,
    SourceType,
)


class SourceDocument(BaseModel):
    """Input document with original text and traceable source metadata."""

    doc_id: str
    title: str | None = None
    author: str | None = None
    source_type: SourceType = SourceType.UNKNOWN
    source_url: str | None = None
    source_file: str | None = None
    source_hash: str | None = None
    published_at: str | None = None
    captured_at: str | None = None
    language: str = "zh-CN"
    raw_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Segment(BaseModel):
    """Paragraph or semantic unit created before chunking."""

    segment_id: str
    doc_id: str
    text_original: str
    text_normalized: str | None = None
    text_cleaned: str | None = None
    paragraph_type: ParagraphType = ParagraphType.UNKNOWN
    content_value: ContentValue = ContentValue.MEDIUM
    action: SegmentAction = SegmentAction.KEEP
    noise_type: NoiseType | None = NoiseType.NONE
    risk_tags: list[RiskTag] = Field(default_factory=list)
    quality_tags: list[QualityTag] = Field(default_factory=list)
    source_position: dict[str, Any] = Field(default_factory=dict)
    repair_count: int = 0
    drop_reason: str | None = None
    review_reason: str | None = None


class RepairRecord(BaseModel):
    """Auditable record for a high-confidence text repair."""

    repair_id: str
    doc_id: str
    segment_id: str
    repair_type: RepairType
    original: str
    fixed: str
    reason: str
    confidence: Confidence


class ReviewRecord(BaseModel):
    """Manual-review item for low-confidence or media-dependent content."""

    review_id: str
    doc_id: str
    segment_id: str
    text: str
    risk_tags: list[RiskTag]
    reason: str
    suggested_action: str | None = None


class Chunk(BaseModel):
    """RAG ingestion chunk with source traceability and embedding text fields."""

    chunk_id: str
    doc_id: str
    chunk_index: int
    title: str | None = None
    section_path: list[str] = Field(default_factory=list)
    text: str
    embedding_text_main: str
    embedding_text_expanded: str | None = None
    source_type: SourceType = SourceType.UNKNOWN
    source_url: str | None = None
    source_file: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    start_time: str | None = None
    end_time: str | None = None
    speaker: str | None = None
    chunk_status: ChunkStatus = ChunkStatus.IMPORT_CHUNK
    chunk_type: ChunkType = ChunkType.MIXED
    quality_tags: list[QualityTag] = Field(default_factory=list)
    risk_tags: list[RiskTag] = Field(default_factory=list)
    repair_count: int = 0
    drop_count: int = 0
    token_estimate: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Manifest(BaseModel):
    """Processing summary for one document output directory."""

    doc_id: str
    source_type: SourceType
    source_hash: str | None = None
    cleaning_version: str = "v0.1.0"
    document_status: DocumentStatus = DocumentStatus.IMPORT_CHUNKED
    total_segments: int
    kept_segments: int
    dropped_segments: int
    review_segments: int
    repair_count: int
    chunk_count: int
    main_drop_reasons: list[str] = Field(default_factory=list)
    main_review_reasons: list[str] = Field(default_factory=list)
    quality_score: float = 100.0
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class CleaningSettings(BaseModel):
    profile: Literal["conservative", "balanced", "aggressive"] = "conservative"
    preserve_original: bool = True
    drop_marketing: bool = True
    drop_footer: bool = True
    drop_copyright: bool = True
    drop_url_only: bool = True
    drop_image_placeholder: bool = True
    keep_short_useful: bool = True


class RepairSettings(BaseModel):
    enable_repair: bool = True
    enable_filler_word_removal: bool = True
    enable_repetition_compression: bool = True
    enable_punctuation_restore: bool = True
    enable_asr_homophone_fix: bool = True
    enable_ocr_character_fix: bool = False
    min_confidence: Confidence = Confidence.HIGH


class ChunkingSettings(BaseModel):
    target_chunk_size_chars: int = 800
    min_chunk_size_chars: int = 120
    max_chunk_size_chars: int = 1500
    overlap_chars: int = 120
    add_section_path_to_text: bool = True


class ExportSettings(BaseModel):
    clean_markdown: bool = True
    chunks_jsonl: bool = True
    manifest_json: bool = True
    repairs_jsonl: bool = True
    review_jsonl: bool = True
    dropped_jsonl: bool = True


class EmbeddingSettings(BaseModel):
    default_text_field: str = "embedding_text_main"
    generate_expanded_text: bool = False


class QualitySettings(BaseModel):
    enable_quality_score: bool = True
    review_on_media_dependency: bool = True
    review_on_semantic_break: bool = True


class CleanerConfig(BaseModel):
    cleaning: CleaningSettings = Field(default_factory=CleaningSettings)
    repair: RepairSettings = Field(default_factory=RepairSettings)
    chunking: ChunkingSettings = Field(default_factory=ChunkingSettings)
    export: ExportSettings = Field(default_factory=ExportSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    quality: QualitySettings = Field(default_factory=QualitySettings)
    rules: dict[str, Any] = Field(default_factory=dict)


class PipelineResult(BaseModel):
    document: SourceDocument
    segments: list[Segment]
    chunks: list[Chunk]
    repairs: list[RepairRecord]
    reviews: list[ReviewRecord]
    manifest: Manifest
    dropped: list[Segment] = Field(default_factory=list)
    output_dir: str | None = None
