from __future__ import annotations

from rag_cleaner_cn.core.models import Chunk


def chunks_missing_source(chunks: list[Chunk]) -> list[str]:
    """Return chunk IDs without a source file or URL."""

    return [chunk.chunk_id for chunk in chunks if not (chunk.source_file or chunk.source_url)]
