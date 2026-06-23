from __future__ import annotations

import json
from pathlib import Path

from rag_cleaner_cn.core.enums import ParagraphType, SegmentAction, SourceType
from rag_cleaner_cn.core.models import Manifest, Segment, SourceDocument
from rag_cleaner_cn.segment.heading import heading_title, is_heading


def write_clean_markdown(
    path: Path,
    document: SourceDocument,
    segments: list[Segment],
    manifest: Manifest,
) -> None:
    """Write clean markdown with YAML-compatible frontmatter."""

    frontmatter = {
        "doc_id": document.doc_id,
        "title": document.title,
        "author_or_account": document.author,
        "source_type": document.source_type.value,
        "source_url": document.source_url,
        "published_at": document.published_at,
        "content_type": _content_type(document.source_type),
        "document_status": manifest.document_status.value,
        "cleaning_version": manifest.cleaning_version,
        "quality_tags": sorted({tag.value for segment in segments for tag in segment.quality_tags}),
    }
    body_lines: list[str] = []
    if document.title and not any(
        is_heading(segment.text_original) and heading_title(segment.text_original) == document.title
        for segment in segments
    ):
        body_lines.extend([f"# {document.title}", ""])
    for segment in segments:
        if segment.action == SegmentAction.DROP or not segment.text_cleaned:
            continue
        if segment.paragraph_type == ParagraphType.HEADING:
            heading = segment.text_cleaned.strip()
            body_lines.append(heading if heading.startswith("#") else f"## {heading}")
        else:
            body_lines.append(segment.text_cleaned.strip())
        body_lines.append("")
    content = "---\n"
    for key, value in frontmatter.items():
        content += f"{key}: {json.dumps(value, ensure_ascii=False)}\n"
    content += "---\n\n"
    content += "\n".join(body_lines).strip() + "\n"
    path.write_text(content, encoding="utf-8")


def _content_type(source_type: SourceType) -> str:
    if source_type in {SourceType.WECHAT_ARTICLE, SourceType.WEB_ARTICLE, SourceType.MARKDOWN}:
        return "article"
    if source_type in {SourceType.VIDEO_TRANSCRIPT, SourceType.AUDIO_TRANSCRIPT}:
        return "transcript_note"
    if source_type == SourceType.COURSE_DOC:
        return "course_note"
    return "document"
