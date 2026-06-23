from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from rag_cleaner_cn.core.enums import ChunkStatus
from rag_cleaner_cn.core.models import PipelineResult
from rag_cleaner_cn.core.pipeline import CleaningPipeline
from rag_cleaner_cn.core.profiles import apply_profile_to_config
from rag_cleaner_cn.eval.acceptance import validate_output_dir
from rag_cleaner_cn.export.jsonl_exporter import read_jsonl, write_jsonl
from rag_cleaner_cn.utils.fileio import ensure_dir

DEFAULT_VECTOR_STATUSES = {ChunkStatus.IMPORT_CHUNK.value, ChunkStatus.IMPORT_SHORT.value}


def apply_profile(pipeline: CleaningPipeline, profile: str | None) -> CleaningPipeline:
    """Apply a CLI profile choice to the pipeline config."""

    apply_profile_to_config(pipeline.config, profile)
    return pipeline


def supported_files(pipeline: CleaningPipeline, input_dir: Path) -> list[Path]:
    """Return supported files in stable path order."""

    supported = {suffix for loader in pipeline.loaders for suffix in loader.supported_suffixes}
    return sorted(
        path for path in input_dir.rglob("*") if path.is_file() and path.suffix.lower() in supported
    )


def select_files(files: list[Path], limit: int | None, sample: int | None) -> list[Path]:
    """Select files by stable limit or random sample."""

    if limit is not None and sample is not None:
        raise ValueError("--limit and --sample cannot be used together")
    if sample is not None:
        return random.sample(files, k=min(sample, len(files)))
    if limit is not None:
        return files[:limit]
    return files


def run_clean_dir_batch(
    pipeline: CleaningPipeline,
    input_dir: Path,
    output_dir: Path,
    *,
    overwrite: bool = False,
    dry_run: bool = False,
    limit: int | None = None,
    sample: int | None = None,
) -> dict[str, Any]:
    """Run safe batch cleaning and write batch_report.json."""

    input_resolved = input_dir.resolve()
    output_resolved = output_dir.resolve()
    if input_resolved == output_resolved:
        raise ValueError("input_dir and output_dir must be different")
    if output_resolved.is_relative_to(input_resolved):
        raise ValueError("output_dir must not be inside input_dir")

    all_files = supported_files(pipeline, input_dir)
    selected_files = select_files(all_files, limit=limit, sample=sample)
    results: list[PipelineResult] = []
    processed_files: list[dict[str, Any]] = []
    ensure_dir(output_dir)

    for path in selected_files:
        if dry_run:
            result = pipeline.process_file(path)
        else:
            result = pipeline.run_file(path, output_dir, overwrite=overwrite)
        results.append(result)
        processed_files.append(
            {
                "input_file": str(path),
                "doc_id": result.document.doc_id,
                "source_type": result.document.source_type.value,
                "output_dir": result.output_dir,
                "chunk_count": result.manifest.chunk_count,
                "quality_score": result.manifest.quality_score,
            }
        )

    report = build_batch_report(
        input_dir=input_dir,
        output_dir=output_dir,
        all_files=all_files,
        selected_files=selected_files,
        results=results,
        processed_files=processed_files,
        profile=pipeline.config.cleaning.profile,
        dry_run=dry_run,
        limit=limit,
        sample=sample,
    )
    write_batch_report(output_dir / "batch_report.json", report)
    return report


def build_batch_report(
    *,
    input_dir: Path,
    output_dir: Path,
    all_files: list[Path],
    selected_files: list[Path],
    results: list[PipelineResult],
    processed_files: list[dict[str, Any]],
    profile: str,
    dry_run: bool,
    limit: int | None,
    sample: int | None,
) -> dict[str, Any]:
    """Build aggregate batch statistics across processed documents."""

    chunk_lengths = [len(chunk.text) for result in results for chunk in result.chunks]
    quality_scores = [result.manifest.quality_score for result in results]
    drop_reasons = Counter(
        segment.drop_reason or (segment.noise_type.value if segment.noise_type else "unknown")
        for result in results
        for segment in result.dropped
    )
    review_reasons = Counter(review.reason for result in results for review in result.reviews)
    chunk_statuses = Counter(
        chunk.chunk_status.value for result in results for chunk in result.chunks
    )
    return {
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "dry_run": dry_run,
        "profile": profile,
        "limit": limit,
        "sample": sample,
        "total_candidates": len(all_files),
        "processed_count": len(results),
        "file_types": dict(Counter(path.suffix.lower() or "<none>" for path in selected_files)),
        "drop_reasons": dict(drop_reasons),
        "review_reasons": dict(review_reasons),
        "chunk_statuses": dict(chunk_statuses),
        "average_chunk_length": round(mean(chunk_lengths), 2) if chunk_lengths else 0.0,
        "quality_score_distribution": _quality_distribution(quality_scores),
        "quality_score_average": round(mean(quality_scores), 2) if quality_scores else 0.0,
        "processed_files": processed_files,
    }


def write_batch_report(path: Path, report: dict[str, Any]) -> None:
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_batch(output_dir: Path) -> dict[str, Any]:
    """Validate every document output directory under a batch output directory."""

    doc_dirs = sorted(path for path in output_dir.iterdir() if path.is_dir())
    errors: dict[str, list[str]] = {}
    for doc_dir in doc_dirs:
        doc_errors = validate_output_dir(doc_dir)
        if doc_errors:
            errors[str(doc_dir)] = doc_errors
    return {
        "output_dir": str(output_dir),
        "checked_count": len(doc_dirs),
        "valid": not errors,
        "errors": errors,
    }


def export_for_vector(
    batch_output_dir: Path,
    output_path: Path,
    *,
    include_status: set[str] | None = None,
) -> int:
    """Collect chunks from a batch output directory into one vector import JSONL."""

    statuses = include_status or DEFAULT_VECTOR_STATUSES
    rows: list[dict[str, Any]] = []
    for chunks_path in sorted(batch_output_dir.glob("*/chunks.jsonl")):
        for row in read_jsonl(chunks_path):
            if row.get("chunk_status") in statuses:
                rows.append(row)
    ensure_dir(output_path.parent)
    write_jsonl(output_path, rows)
    return len(rows)


def _quality_distribution(scores: list[float]) -> dict[str, int]:
    buckets = {"90-100": 0, "80-89": 0, "60-79": 0, "0-59": 0}
    for score in scores:
        if score >= 90:
            buckets["90-100"] += 1
        elif score >= 80:
            buckets["80-89"] += 1
        elif score >= 60:
            buckets["60-79"] += 1
        else:
            buckets["0-59"] += 1
    return buckets
