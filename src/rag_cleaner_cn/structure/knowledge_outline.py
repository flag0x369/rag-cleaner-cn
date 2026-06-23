from __future__ import annotations

import re

from rag_cleaner_cn.core.enums import (
    ContentValue,
    ParagraphType,
    QualityTag,
    SegmentAction,
    SourceType,
)
from rag_cleaner_cn.core.models import Segment, SourceDocument

_AUTO_STRUCTURE_MIN_CHARS = 1500
_GENERIC_HEADINGS = ("核心观点", "关键论述", "结尾")
_ARTICLE_SOURCE_TYPES = {
    SourceType.WECHAT_ARTICLE,
    SourceType.WEB_ARTICLE,
    SourceType.MARKDOWN,
    SourceType.PLAIN_TEXT,
}
_ENDING_PUNCTUATION = "。！？!?；;：:"
_INLINE_PUNCTUATION = "，,。！？!?；;：:"
_NON_HEADING_PREFIXES = (
    "这是",
    "关注",
    "愿你",
    "点击",
    "宝子们",
    "大家好",
)


def enhance_knowledge_structure(
    document: SourceDocument,
    segments: list[Segment],
) -> list[Segment]:
    """Make markdown more scannable without rewriting body text."""

    if document.source_type not in _ARTICLE_SOURCE_TYPES:
        return segments
    promoted = _promote_original_subheadings(segments)
    if _needs_generic_anchors(promoted):
        return _insert_generic_anchors(document, promoted)
    return promoted


def _promote_original_subheadings(segments: list[Segment]) -> list[Segment]:
    for index, segment in enumerate(segments):
        if segment.action == SegmentAction.DROP or segment.paragraph_type == ParagraphType.HEADING:
            continue
        text = (segment.text_cleaned or "").strip()
        next_text = _next_body_text(segments, index)
        if _looks_like_original_subheading(text, next_text):
            segment.paragraph_type = ParagraphType.HEADING
            segment.content_value = ContentValue.HIGH
    return segments


def _looks_like_original_subheading(text: str, next_text: str | None) -> bool:
    if not next_text or len(next_text) < 8:
        return False
    if not (6 <= len(text) <= 48):
        return False
    if text.startswith("#") or re.match(r"^([-*+]|\d+[.、])\s*", text):
        return False
    if any(text.startswith(prefix) for prefix in _NON_HEADING_PREFIXES):
        return False
    if text.endswith(tuple(_ENDING_PUNCTUATION)):
        return False
    if any(char in text for char in _INLINE_PUNCTUATION):
        return False
    return bool(re.search(r"[\u4e00-\u9fff]{2,}", text))


def _next_body_text(segments: list[Segment], index: int) -> str | None:
    for segment in segments[index + 1 :]:
        if segment.action == SegmentAction.DROP or segment.paragraph_type == ParagraphType.HEADING:
            continue
        text = (segment.text_cleaned or "").strip()
        if text:
            return text
    return None


def _needs_generic_anchors(segments: list[Segment]) -> bool:
    body_chars = sum(
        len(segment.text_cleaned or "")
        for segment in segments
        if segment.action != SegmentAction.DROP and segment.paragraph_type != ParagraphType.HEADING
    )
    return body_chars >= _AUTO_STRUCTURE_MIN_CHARS and _subheading_count(segments) < 2


def _subheading_count(segments: list[Segment]) -> int:
    return sum(
        1
        for segment in segments
        if segment.paragraph_type == ParagraphType.HEADING
        and not (segment.text_cleaned or segment.text_original).lstrip().startswith("# ")
    )


def _insert_generic_anchors(document: SourceDocument, segments: list[Segment]) -> list[Segment]:
    body_indices = [
        index
        for index, segment in enumerate(segments)
        if segment.action != SegmentAction.DROP
        and segment.paragraph_type != ParagraphType.HEADING
        and (segment.text_cleaned or "").strip()
    ]
    if len(body_indices) < 3:
        return segments

    anchor_indices = {
        body_indices[0]: _GENERIC_HEADINGS[0],
        body_indices[len(body_indices) // 3]: _GENERIC_HEADINGS[1],
        body_indices[(len(body_indices) * 2) // 3]: _GENERIC_HEADINGS[2],
    }
    enhanced: list[Segment] = []
    generated_index = 1
    for index, segment in enumerate(segments):
        heading = anchor_indices.get(index)
        if heading:
            enhanced.append(_generic_heading_segment(document.doc_id, generated_index, heading))
            generated_index += 1
        enhanced.append(segment)
    return enhanced


def _generic_heading_segment(doc_id: str, index: int, heading: str) -> Segment:
    return Segment(
        segment_id=f"{doc_id}_struct_{index:04d}",
        doc_id=doc_id,
        text_original=heading,
        text_cleaned=heading,
        paragraph_type=ParagraphType.HEADING,
        content_value=ContentValue.HIGH,
        action=SegmentAction.KEEP,
        quality_tags=[QualityTag.WEAK_STRUCTURE],
        source_position={"generated": "generic_structure_anchor"},
    )
