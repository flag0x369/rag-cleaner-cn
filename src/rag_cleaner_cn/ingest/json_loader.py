from __future__ import annotations

import json
from pathlib import Path

from rag_cleaner_cn.core.enums import SourceType
from rag_cleaner_cn.core.models import SourceDocument
from rag_cleaner_cn.ingest.base import build_source_document


class JsonLoader:
    supported_suffixes = {".json", ".jsonl"}

    def load(self, path: Path, source_type: SourceType | None = None) -> SourceDocument:
        records = _read_records(path)
        first = records[0] if records else {}
        raw_text = "\n\n".join(str(record.get("content", "")) for record in records).strip()
        parsed_type = _source_type(str(first.get("source_type") or "unknown"))
        return build_source_document(
            raw_text,
            path=path,
            source_type=source_type or parsed_type,
            title=first.get("title") or path.stem,
            author=first.get("author"),
            source_url=first.get("source_url"),
            published_at=first.get("published_at"),
            metadata={"record_count": len(records)},
        )


def _read_records(path: Path) -> list[dict]:
    if path.suffix.lower() == ".jsonl":
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [record for record in data if isinstance(record, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def _source_type(value: str) -> SourceType:
    try:
        return SourceType(value)
    except ValueError:
        return SourceType.UNKNOWN
