from __future__ import annotations

import re
from pathlib import Path

from rag_cleaner_cn.core.enums import SourceType
from rag_cleaner_cn.core.models import SourceDocument
from rag_cleaner_cn.ingest.base import build_source_document


class MarkdownLoader:
    supported_suffixes = {".md", ".markdown"}

    def load(self, path: Path, source_type: SourceType | None = None) -> SourceDocument:
        raw_text = path.read_text(encoding="utf-8")
        cleaned_text, inline_metadata = _extract_inline_source_metadata(raw_text)
        detected_source_type = (
            source_type or _detect_source_type(inline_metadata) or SourceType.MARKDOWN
        )
        return build_source_document(
            cleaned_text,
            path=path,
            source_type=detected_source_type,
            title=_first_heading(cleaned_text) or path.stem,
            author=inline_metadata.get("author"),
            source_url=inline_metadata.get("source_url"),
            published_at=inline_metadata.get("published_at"),
            metadata={
                key: value
                for key, value in inline_metadata.items()
                if key not in {"author", "source_url", "published_at"}
            },
        )


def _first_heading(text: str) -> str | None:
    match = re.search(r"^#[ \t]+(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def _extract_inline_source_metadata(text: str) -> tuple[str, dict[str, str]]:
    metadata: dict[str, str] = {}
    body_lines: list[str] = []
    for line in text.splitlines():
        key, value = _parse_source_metadata_line(line)
        if key:
            if value:
                metadata.setdefault(key, value)
            if value and line.strip().startswith("公众号"):
                metadata.setdefault("source_type", SourceType.WECHAT_ARTICLE.value)
            continue
        body_lines.append(line)
    return "\n".join(body_lines).strip(), metadata


def _parse_source_metadata_line(line: str) -> tuple[str | None, str]:
    stripped = line.strip()
    patterns = [
        ("author", r"^(公众号|账号|作者|来源)[:：]\s*(.+)$"),
        ("published_at", r"^(发布时间|发布日期|发布于)[:：]\s*(.*)$"),
        ("source_url", r"^(原文|原文链接|链接|URL)[:：]\s*(https?://\S+).*$"),
    ]
    for key, pattern in patterns:
        match = re.match(pattern, stripped, flags=re.IGNORECASE)
        if match:
            return key, match.group(2).strip()
    return None, ""


def _detect_source_type(metadata: dict[str, str]) -> SourceType | None:
    value = metadata.get("source_type")
    if value:
        return SourceType(value)
    return None
