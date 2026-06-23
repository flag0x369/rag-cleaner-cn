from __future__ import annotations

from collections import Counter
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from rag_cleaner_cn.chunk.semantic_chunker import build_chunks
from rag_cleaner_cn.clean.cleaner import clean_segments
from rag_cleaner_cn.core.enums import DocumentStatus, SourceType
from rag_cleaner_cn.core.errors import OutputExistsError, UnsupportedInputError
from rag_cleaner_cn.core.models import (
    CleanerConfig,
    Manifest,
    PipelineResult,
    SourceDocument,
)
from rag_cleaner_cn.core.profiles import apply_profile_to_config
from rag_cleaner_cn.export.jsonl_exporter import write_jsonl
from rag_cleaner_cn.export.manifest_exporter import write_manifest
from rag_cleaner_cn.export.markdown_exporter import write_clean_markdown
from rag_cleaner_cn.ingest.base import Loader, build_source_document
from rag_cleaner_cn.ingest.html_loader import HtmlLoader
from rag_cleaner_cn.ingest.json_loader import JsonLoader
from rag_cleaner_cn.ingest.markdown_loader import MarkdownLoader
from rag_cleaner_cn.ingest.pdf_loader import PdfLoader
from rag_cleaner_cn.ingest.text_loader import TextLoader
from rag_cleaner_cn.ingest.transcript_loader import TranscriptLoader
from rag_cleaner_cn.repair.repairer import repair_segments
from rag_cleaner_cn.repair.review_marker import build_review_records
from rag_cleaner_cn.segment.segmenter import segment_text
from rag_cleaner_cn.structure.knowledge_outline import enhance_knowledge_structure
from rag_cleaner_cn.utils.fileio import ensure_dir

CLEANING_VERSION = "v0.1.0"


class CleaningPipeline:
    """Main local processing pipeline from source document to RAG-ready assets."""

    def __init__(self, config: CleanerConfig):
        self.config = config
        self.loaders: list[Loader] = [
            MarkdownLoader(),
            TextLoader(),
            HtmlLoader(),
            TranscriptLoader(),
            PdfLoader(),
            JsonLoader(),
        ]

    @classmethod
    def default(cls) -> CleaningPipeline:
        return cls(load_default_config())

    @classmethod
    def from_config_file(cls, path: Path) -> CleaningPipeline:
        return cls(load_default_config(path))

    def run_file(
        self,
        input_path: Path,
        output_dir: Path,
        source_type: SourceType | None = None,
        overwrite: bool = False,
    ) -> PipelineResult:
        """Run the full pipeline for one file and export a document output directory."""

        result = self.process_file(input_path, source_type=source_type)
        document = result.document
        doc_output_dir = output_dir / document.doc_id
        if doc_output_dir.exists() and any(doc_output_dir.iterdir()) and not overwrite:
            raise OutputExistsError(
                f"output directory already exists: {doc_output_dir}. Use --overwrite to replace files."
            )
        ensure_dir(doc_output_dir)
        self._export(result, doc_output_dir)
        result.output_dir = str(doc_output_dir)
        return result

    def process_file(
        self,
        input_path: Path,
        source_type: SourceType | None = None,
    ) -> PipelineResult:
        """Run the full pipeline for one file without exporting artifacts."""

        document = self._load_document(input_path, source_type)
        return self._run_document(document)

    def run_text(self, text: str, metadata: dict | None = None) -> PipelineResult:
        """Run the full pipeline for raw text without writing files."""

        metadata = metadata or {}
        source_type = _coerce_source_type(metadata.get("source_type")) or SourceType.PLAIN_TEXT
        document = build_source_document(
            text,
            source_type=source_type,
            title=metadata.get("title"),
            author=metadata.get("author"),
            source_url=metadata.get("source_url"),
            published_at=metadata.get("published_at"),
            metadata={key: value for key, value in metadata.items() if key not in {"content"}},
        )
        return self._run_document(document)

    def _load_document(self, input_path: Path, source_type: SourceType | None) -> SourceDocument:
        suffix = input_path.suffix.lower()
        for loader in self.loaders:
            if suffix in loader.supported_suffixes:
                return loader.load(input_path, source_type=source_type)
        raise UnsupportedInputError(f"Unsupported input suffix: {suffix}")

    def _run_document(self, document: SourceDocument) -> PipelineResult:
        transcript_cues = document.metadata.get("transcript_cues")
        segments = segment_text(
            document.raw_text, doc_id=document.doc_id, transcript_cues=transcript_cues
        )
        kept_segments, dropped_segments = clean_segments(segments, self.config.rules)
        kept_segments, repairs = repair_segments(kept_segments, self.config)
        kept_segments = enhance_knowledge_structure(document, kept_segments)
        reviews = build_review_records(kept_segments)
        chunks = build_chunks(
            document, kept_segments, self.config, drop_count=len(dropped_segments)
        )
        manifest = build_manifest(
            document, kept_segments, dropped_segments, reviews, repairs, chunks
        )
        return PipelineResult(
            document=document,
            segments=kept_segments,
            chunks=chunks,
            repairs=repairs,
            reviews=reviews,
            manifest=manifest,
            dropped=dropped_segments,
        )

    def _export(self, result: PipelineResult, output_dir: Path) -> None:
        if self.config.export.clean_markdown:
            write_clean_markdown(
                output_dir / "clean.md",
                result.document,
                result.segments,
                result.manifest,
            )
        if self.config.export.chunks_jsonl:
            write_jsonl(output_dir / "chunks.jsonl", result.chunks)
        if self.config.export.manifest_json:
            write_manifest(output_dir / "manifest.json", result.manifest)
        if self.config.export.repairs_jsonl:
            write_jsonl(output_dir / "repairs.jsonl", result.repairs)
        if self.config.export.review_jsonl:
            write_jsonl(output_dir / "review.jsonl", result.reviews)
        if self.config.export.dropped_jsonl:
            write_jsonl(
                output_dir / "dropped.jsonl", [_dropped_row(segment) for segment in result.dropped]
            )


def build_manifest(
    document: SourceDocument,
    kept_segments,
    dropped_segments,
    reviews,
    repairs,
    chunks,
) -> Manifest:
    drop_reasons = Counter(
        segment.drop_reason or str(segment.noise_type) for segment in dropped_segments
    )
    review_reasons = Counter(review.reason for review in reviews)
    if not chunks:
        status = DocumentStatus.EXCLUDE
    elif reviews:
        status = DocumentStatus.REVIEW
    else:
        status = DocumentStatus.IMPORT_CHUNKED
    quality_score = _quality_score(
        total=len(kept_segments) + len(dropped_segments),
        dropped=len(dropped_segments),
        reviews=len(reviews),
        repairs=len(repairs),
        chunks=chunks,
        source_missing=not (document.source_file or document.source_url),
    )
    return Manifest(
        doc_id=document.doc_id,
        source_type=document.source_type,
        source_hash=document.source_hash,
        cleaning_version=CLEANING_VERSION,
        document_status=status,
        total_segments=len(kept_segments) + len(dropped_segments),
        kept_segments=len(kept_segments),
        dropped_segments=len(dropped_segments),
        review_segments=len(reviews),
        repair_count=len(repairs),
        chunk_count=len(chunks),
        main_drop_reasons=[reason for reason, _ in drop_reasons.most_common(5)],
        main_review_reasons=[reason for reason, _ in review_reasons.most_common(5)],
        quality_score=quality_score,
    )


def load_default_config(config_path: Path | None = None) -> CleanerConfig:
    """Load packaged defaults, packaged rules, and optional YAML overrides."""

    default_config = _read_packaged_yaml("default_config.yaml")
    default_rules = _read_packaged_yaml("default_rules.yaml")
    merged: dict[str, Any] = {**default_config, "rules": default_rules}
    if config_path:
        override = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        merged = _deep_merge(merged, override)
    return apply_profile_to_config(CleanerConfig.model_validate(merged))


def _read_packaged_yaml(filename: str) -> dict[str, Any]:
    package_files = resources.files("rag_cleaner_cn.config")
    with resources.as_file(package_files / filename) as path:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _coerce_source_type(value: Any) -> SourceType | None:
    if value is None or isinstance(value, SourceType):
        return value
    try:
        return SourceType(str(value))
    except ValueError:
        return SourceType.UNKNOWN


def _quality_score(
    total: int,
    dropped: int,
    reviews: int,
    repairs: int,
    chunks,
    source_missing: bool,
) -> float:
    score = 100.0
    if total:
        score -= min(20.0, dropped / total * 20)
        score -= min(30.0, reviews / total * 30)
    score -= min(10.0, repairs * 1.0)
    if source_missing:
        score -= 5.0
    for chunk in chunks:
        if chunk.token_estimate and chunk.token_estimate > 1800:
            score -= 2.0
        if not chunk.section_path and len(chunk.text) < 80:
            score -= 1.0
        if chunk.risk_tags:
            score -= 2.0
    return round(max(0.0, min(100.0, score)), 2)


def _dropped_row(segment) -> dict[str, Any]:
    return {
        "segment_id": segment.segment_id,
        "doc_id": segment.doc_id,
        "text": segment.text_original,
        "noise_type": segment.noise_type.value if segment.noise_type else None,
        "reason": segment.drop_reason,
        "confidence": "high",
    }
