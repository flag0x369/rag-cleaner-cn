from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from rag_cleaner_cn.core.enums import SourceType
from rag_cleaner_cn.core.models import SourceDocument
from rag_cleaner_cn.ingest.base import build_source_document

NO_EXTRACTABLE_TEXT_MESSAGE = (
    "This PDF appears to have little or no extractable text. OCR is not enabled by default."
)


class PdfLoader:
    supported_suffixes = {".pdf"}

    def load(self, path: Path, source_type: SourceType | None = None) -> SourceDocument:
        reader = PdfReader(str(path))
        pages: list[str] = []
        for page_index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"\n\n<!-- page:{page_index} -->\n\n{text.strip()}")
        raw_text = "\n".join(pages).strip() or NO_EXTRACTABLE_TEXT_MESSAGE
        return build_source_document(
            raw_text,
            path=path,
            source_type=source_type or SourceType.PDF,
            metadata={"pdf_pages": len(reader.pages), "ocr_enabled": False},
        )
