from __future__ import annotations

from pathlib import Path

from rag_cleaner_cn.core.enums import SourceType
from rag_cleaner_cn.core.models import SourceDocument
from rag_cleaner_cn.ingest.base import build_source_document


class TextLoader:
    supported_suffixes = {".txt"}

    def load(self, path: Path, source_type: SourceType | None = None) -> SourceDocument:
        return build_source_document(
            path.read_text(encoding="utf-8"),
            path=path,
            source_type=source_type or SourceType.PLAIN_TEXT,
        )
