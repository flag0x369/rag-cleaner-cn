from __future__ import annotations

from rag_cleaner_cn.core.enums import SegmentAction
from rag_cleaner_cn.core.models import ReviewRecord, Segment
from rag_cleaner_cn.utils.ids import review_id


def build_review_records(segments: list[Segment]) -> list[ReviewRecord]:
    """Create review records for segments marked review or carrying risk tags."""

    reviews: list[ReviewRecord] = []
    for segment in segments:
        if segment.action != SegmentAction.REVIEW and not segment.risk_tags:
            continue
        reason = segment.review_reason or "存在低置信风险，需要人工复核"
        reviews.append(
            ReviewRecord(
                review_id=review_id(len(reviews) + 1),
                doc_id=segment.doc_id,
                segment_id=segment.segment_id,
                text=segment.text_cleaned or segment.text_normalized or segment.text_original,
                risk_tags=segment.risk_tags,
                reason=reason,
                suggested_action="人工查看原始资料或上下文",
            )
        )
    return reviews
