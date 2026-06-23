from __future__ import annotations

import json
from pathlib import Path

from rag_cleaner_cn.classify.noise_classifier import classify_noise
from rag_cleaner_cn.core.enums import NoiseType
from rag_cleaner_cn.core.pipeline import load_default_config
from rag_cleaner_cn.export.jsonl_exporter import read_jsonl


def validate_output_dir(path: Path) -> list[str]:
    """Validate required output files and basic manifest consistency."""

    errors: list[str] = []
    required = [
        "clean.md",
        "chunks.jsonl",
        "manifest.json",
        "repairs.jsonl",
        "review.jsonl",
        "dropped.jsonl",
    ]
    for filename in required:
        if not (path / filename).exists():
            errors.append(f"missing {filename}")
    chunks = read_jsonl(path / "chunks.jsonl")
    for index, chunk in enumerate(chunks, start=1):
        if not chunk.get("doc_id"):
            errors.append(f"chunk {index} missing doc_id")
        if not chunk.get("chunk_id"):
            errors.append(f"chunk {index} missing chunk_id")
        if not str(chunk.get("text", "")).strip():
            errors.append(f"chunk {index} empty text")
        if chunk.get("chunk_status") == "review_chunk":
            if not chunk.get("risk_tags"):
                errors.append(f"review_chunk {chunk.get('chunk_id')} missing risk_tags")
            if not chunk.get("metadata", {}).get("review_reasons"):
                errors.append(f"review_chunk {chunk.get('chunk_id')} missing review_reasons")
    for row in read_jsonl(path / "repairs.jsonl"):
        if not row.get("original") or not row.get("fixed"):
            errors.append(f"repair {row.get('repair_id')} missing original/fixed")
    manifest_path = path / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("chunk_count") != len(chunks):
            errors.append("manifest chunk_count does not match chunks.jsonl")
        repairs = read_jsonl(path / "repairs.jsonl")
        if manifest.get("repair_count") != len(repairs):
            errors.append("manifest repair_count does not match repairs.jsonl")
        reviews = read_jsonl(path / "review.jsonl")
        if manifest.get("review_segments") != len(reviews):
            errors.append("manifest review_segments does not match review.jsonl")
        dropped = read_jsonl(path / "dropped.jsonl")
        if manifest.get("dropped_segments") != len(dropped):
            errors.append("manifest dropped_segments does not match dropped.jsonl")
    return errors


def acceptance_checks(path: Path) -> list[str]:
    """Run lightweight acceptance checks for obvious RAG-cleaning regressions."""

    issues = validate_output_dir(path)
    clean_text = (
        (path / "clean.md").read_text(encoding="utf-8") if (path / "clean.md").exists() else ""
    )
    if _contains_obvious_noise(clean_text):
        issues.append("clean.md still contains obvious marketing or QR noise")
    if "版权所有" in clean_text or "转载请注明" in clean_text:
        issues.append("clean.md still contains obvious footer/copyright text")
    chunks = read_jsonl(path / "chunks.jsonl")
    for chunk in chunks:
        text = str(chunk.get("text", ""))
        if len(text) > 1800:
            issues.append(f"{chunk.get('chunk_id')} is too long")
        if len(text) < 10:
            issues.append(f"{chunk.get('chunk_id')} is too short")
        if not (chunk.get("source_file") or chunk.get("source_url")):
            issues.append(f"{chunk.get('chunk_id')} has no source reference")
    return issues


def _contains_obvious_noise(clean_text: str) -> bool:
    rules = load_default_config().rules
    for line in _markdown_body_lines(clean_text):
        noise_type, _ = classify_noise(line, rules)
        if noise_type in {NoiseType.MARKETING, NoiseType.IMAGE_PLACEHOLDER}:
            return True
    return False


def _markdown_body_lines(clean_text: str) -> list[str]:
    lines = clean_text.splitlines()
    if lines[:1] == ["---"]:
        for index, line in enumerate(lines[1:], start=1):
            if line == "---":
                lines = lines[index + 1 :]
                break
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]
