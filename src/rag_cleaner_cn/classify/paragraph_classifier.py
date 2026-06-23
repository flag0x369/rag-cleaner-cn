from __future__ import annotations

import re

from rag_cleaner_cn.core.enums import ContentValue, ParagraphType, QualityTag
from rag_cleaner_cn.segment.heading import is_heading


def classify_paragraph(
    text: str, current_type: ParagraphType = ParagraphType.UNKNOWN
) -> tuple[ParagraphType, ContentValue, list[QualityTag]]:
    """Classify a paragraph by function, not by isolated keywords."""

    stripped = text.strip()
    quality_tags: list[QualityTag] = []
    if current_type in {ParagraphType.HEADING, ParagraphType.TITLE} or is_heading(stripped):
        return ParagraphType.HEADING, ContentValue.HIGH, quality_tags
    if current_type == ParagraphType.TRANSCRIPT_SPEECH:
        return ParagraphType.TRANSCRIPT_SPEECH, ContentValue.MEDIUM, quality_tags
    if not stripped:
        return ParagraphType.NOISE, ContentValue.NONE, quality_tags
    if len(stripped) < 40 and _has_claim_signal(stripped):
        quality_tags.append(QualityTag.SHORT_BUT_USEFUL)
        return ParagraphType.BODY_CLAIM, ContentValue.HIGH, quality_tags
    if stripped.endswith(("？", "?")):
        return ParagraphType.QUESTION, ContentValue.HIGH, quality_tags
    if re.match(r"^(答|讲师|老师)[:：]", stripped):
        return ParagraphType.ANSWER, ContentValue.HIGH, quality_tags
    if re.search(r"(是指|指的是|定义为|所谓|本质是)", stripped):
        return ParagraphType.DEFINITION, ContentValue.HIGH, quality_tags
    if re.search(r"(第一步|第二步|第三步|步骤|流程|操作|先.+再|最后)", stripped):
        return ParagraphType.STEP, ContentValue.HIGH, quality_tags
    if re.search(r"(方法|原则|策略|模型|框架|判断标准)", stripped):
        return ParagraphType.METHOD, ContentValue.HIGH, quality_tags
    if re.search(r"(例如|比如|案例|学员|公司|项目)", stripped):
        return ParagraphType.CASE, ContentValue.MEDIUM, quality_tags
    if re.match(r"^([-*+]|\d+[.、])\s*", stripped):
        return ParagraphType.LIST, ContentValue.MEDIUM, quality_tags
    if _has_claim_signal(stripped):
        return ParagraphType.BODY_CLAIM, ContentValue.HIGH, quality_tags
    return ParagraphType.UNKNOWN, ContentValue.MEDIUM, quality_tags


def _has_claim_signal(text: str) -> bool:
    return bool(
        re.search(r"(不是.+而是|关键|核心|本质|意味着|取决于|决定了|应该|必须|不能|需要)", text)
    )
