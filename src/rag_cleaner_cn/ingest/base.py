from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from rag_cleaner_cn.core.enums import SourceType
from rag_cleaner_cn.core.models import SourceDocument
from rag_cleaner_cn.utils.hashing import sha256_file, sha256_text, stable_doc_id


class Loader(Protocol):
    supported_suffixes: set[str]

    def load(self, path: Path, source_type: SourceType | None = None) -> SourceDocument: ...


def build_source_document(
    raw_text: str,
    path: Path | None = None,
    source_type: SourceType = SourceType.UNKNOWN,
    title: str | None = None,
    author: str | None = None,
    source_url: str | None = None,
    published_at: str | None = None,
    metadata: dict | None = None,
) -> SourceDocument:
    source_hash = sha256_file(path) if path else sha256_text(raw_text)
    identifier = str(path.resolve()) + source_hash if path else raw_text[:200] + source_hash
    return SourceDocument(
        doc_id=stable_doc_id(identifier),
        title=title or (path.stem if path else None),
        author=author,
        source_type=source_type,
        source_url=source_url,
        source_file=str(path) if path else None,
        source_hash=source_hash,
        published_at=published_at,
        captured_at=datetime.now(UTC).isoformat(),
        raw_text=raw_text,
        metadata=metadata or {},
    )
