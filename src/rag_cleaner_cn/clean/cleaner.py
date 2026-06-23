from __future__ import annotations

import re

from rag_cleaner_cn.classify.noise_classifier import classify_noise
from rag_cleaner_cn.classify.paragraph_classifier import classify_paragraph
from rag_cleaner_cn.classify.risk_classifier import classify_risks
from rag_cleaner_cn.core.enums import NoiseType, QualityTag, SegmentAction
from rag_cleaner_cn.core.models import Segment
from rag_cleaner_cn.normalize.markdown import strip_html_residue
from rag_cleaner_cn.normalize.punctuation import normalize_punctuation
from rag_cleaner_cn.normalize.whitespace import normalize_whitespace


def clean_segments(segments: list[Segment], rules: dict) -> tuple[list[Segment], list[Segment]]:
    """Normalize and conservatively drop only whole paragraphs that are deterministic noise."""

    kept: list[Segment] = []
    dropped: list[Segment] = []
    for segment in segments:
        text = segment.text_normalized or segment.text_original
        normalized = normalize_punctuation(strip_html_residue(normalize_whitespace(text)))
        segment.text_normalized = normalized

        noise_type, drop_reason = classify_noise(normalized, rules)
        if noise_type is not NoiseType.NONE:
            segment.text_cleaned = None
            segment.action = SegmentAction.DROP
            segment.noise_type = noise_type
            segment.drop_reason = drop_reason
            if noise_type is NoiseType.MARKETING:
                segment.quality_tags.append(QualityTag.MARKETING_REMOVED)
            if noise_type in {NoiseType.FOOTER, NoiseType.COPYRIGHT}:
                segment.quality_tags.append(QualityTag.FOOTER_REMOVED)
            dropped.append(segment)
            continue

        paragraph_type, content_value, quality_tags = classify_paragraph(
            normalized, segment.paragraph_type
        )
        risks, review_reason = classify_risks(normalized)
        segment.paragraph_type = paragraph_type
        segment.content_value = content_value
        segment.quality_tags.extend(tag for tag in quality_tags if tag not in segment.quality_tags)
        segment.risk_tags.extend(tag for tag in risks if tag not in segment.risk_tags)
        segment.text_cleaned = normalized
        segment.noise_type = NoiseType.NONE
        if risks:
            segment.action = SegmentAction.REVIEW
            segment.review_reason = review_reason
            if QualityTag.NEEDS_REVIEW not in segment.quality_tags:
                segment.quality_tags.append(QualityTag.NEEDS_REVIEW)
        else:
            segment.action = SegmentAction.KEEP
            if QualityTag.CLEAN not in segment.quality_tags:
                segment.quality_tags.append(QualityTag.CLEAN)
        kept.append(segment)
    kept, dropped = _trim_inline_trailing_footer_blocks(kept, dropped, rules)
    kept, dropped = _drop_trailing_footer_blocks(kept, dropped, rules)
    return kept, dropped


def _trim_inline_trailing_footer_blocks(
    kept: list[Segment], dropped: list[Segment], rules: dict
) -> tuple[list[Segment], list[Segment]]:
    start_patterns = rules.get("inline_trailing_footer_start_patterns", [])
    evidence_patterns = rules.get("trailing_footer_evidence_patterns", [])
    if not start_patterns or not evidence_patterns:
        return kept, dropped

    new_kept: list[Segment] = []
    for segment in kept:
        text = _segment_text(segment)
        start_index = _find_inline_footer_start(text, start_patterns, evidence_patterns)
        if start_index is None:
            new_kept.append(segment)
            continue

        prefix = text[:start_index].strip()
        tail = text[start_index:].strip()
        if not prefix or not tail:
            new_kept.append(segment)
            continue

        segment.text_normalized = prefix
        segment.text_cleaned = prefix
        dropped.append(_build_dropped_tail_segment(segment, tail))
        new_kept.append(segment)
    return new_kept, dropped


def _drop_trailing_footer_blocks(
    kept: list[Segment], dropped: list[Segment], rules: dict
) -> tuple[list[Segment], list[Segment]]:
    start_patterns = rules.get("trailing_footer_start_patterns", [])
    evidence_patterns = rules.get("trailing_footer_evidence_patterns", [])
    if not start_patterns or not evidence_patterns:
        return kept, dropped

    start_index = None
    for index, segment in enumerate(kept):
        text = _segment_text(segment)
        if _matches_any(text, start_patterns) and _tail_has_evidence(
            kept[index + 1 :], evidence_patterns
        ):
            start_index = index
            break
    if start_index is None:
        return kept, dropped

    new_kept = kept[:start_index]
    for segment in kept[start_index:]:
        segment.text_cleaned = None
        segment.action = SegmentAction.DROP
        segment.noise_type = NoiseType.MARKETING
        segment.drop_reason = "尾部推广区块"
        if QualityTag.MARKETING_REMOVED not in segment.quality_tags:
            segment.quality_tags.append(QualityTag.MARKETING_REMOVED)
        dropped.append(segment)
    return new_kept, dropped


def _find_inline_footer_start(
    text: str, start_patterns: list[str], evidence_patterns: list[str]
) -> int | None:
    for pattern in start_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        tail = text[match.start() :]
        if tail.strip() and _matches_any(tail, evidence_patterns):
            return match.start()
    return None


def _build_dropped_tail_segment(segment: Segment, tail: str) -> Segment:
    dropped_segment = segment.model_copy(deep=True)
    dropped_segment.segment_id = f"{segment.segment_id}_tail_drop"
    dropped_segment.text_original = tail
    dropped_segment.text_normalized = tail
    dropped_segment.text_cleaned = None
    dropped_segment.action = SegmentAction.DROP
    dropped_segment.noise_type = NoiseType.MARKETING
    dropped_segment.drop_reason = "尾部推广区块"
    dropped_segment.review_reason = None
    dropped_segment.risk_tags = []
    if QualityTag.MARKETING_REMOVED not in dropped_segment.quality_tags:
        dropped_segment.quality_tags.append(QualityTag.MARKETING_REMOVED)
    return dropped_segment


def _tail_has_evidence(segments: list[Segment], patterns: list[str]) -> bool:
    return any(_matches_any(_segment_text(segment), patterns) for segment in segments)


def _segment_text(segment: Segment) -> str:
    return (segment.text_cleaned or segment.text_normalized or segment.text_original).strip()


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)
