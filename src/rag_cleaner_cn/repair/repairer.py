from __future__ import annotations

from rag_cleaner_cn.core.enums import Confidence, RepairType, SegmentAction
from rag_cleaner_cn.core.models import CleanerConfig, RepairRecord, Segment
from rag_cleaner_cn.repair.asr_rules import apply_asr_homophone_rules
from rag_cleaner_cn.repair.filler_words import remove_filler_words
from rag_cleaner_cn.repair.ocr_rules import apply_ocr_rules
from rag_cleaner_cn.repair.punctuation_restore import restore_step_punctuation
from rag_cleaner_cn.repair.repetition import compress_repetition
from rag_cleaner_cn.utils.ids import repair_id


def repair_segments(
    segments: list[Segment],
    config: CleanerConfig,
) -> tuple[list[Segment], list[RepairRecord]]:
    """Apply conservative high-confidence repairs and record every substantive change."""

    if not config.repair.enable_repair:
        return segments, []

    records: list[RepairRecord] = []
    context = "\n".join(segment.text_cleaned or "" for segment in segments)
    for segment in segments:
        if segment.action == SegmentAction.DROP:
            continue
        text = segment.text_cleaned or segment.text_normalized or segment.text_original

        if config.repair.enable_filler_word_removal:
            text = _apply_repair(
                segment,
                text,
                records,
                lambda value: remove_filler_words(
                    value, list(config.rules.get("filler_words", []))
                ),
                RepairType.FILLER_WORD_REMOVAL,
                "删除无意义语气填充词，未改变核心语义",
            )
        if config.repair.enable_repetition_compression:
            text = _apply_repair(
                segment,
                text,
                records,
                compress_repetition,
                RepairType.REPETITION_COMPRESSION,
                "压缩明显卡顿重复",
            )
        if config.repair.enable_punctuation_restore:
            text = _apply_repair(
                segment,
                text,
                records,
                restore_step_punctuation,
                RepairType.PUNCTUATION_RESTORE,
                "恢复步骤类转写文本的基本标点",
            )
        if config.repair.enable_asr_homophone_fix:
            text = _apply_repair(
                segment,
                text,
                records,
                lambda value: apply_asr_homophone_rules(
                    value,
                    dict(config.rules.get("asr_homophone_candidates", {})),
                    context,
                ),
                RepairType.ASR_HOMOPHONE_FIX,
                "结合上下文进行高置信 ASR 同音错词修复",
            )
        if config.repair.enable_ocr_character_fix:
            text = _apply_repair(
                segment,
                text,
                records,
                apply_ocr_rules,
                RepairType.OCR_CHARACTER_FIX,
                "高置信 OCR 字符修复",
            )

        segment.text_cleaned = text
    return segments, records


def _apply_repair(
    segment: Segment,
    text: str,
    records: list[RepairRecord],
    fixer,
    repair_type: RepairType,
    reason: str,
) -> str:
    fixed, changed = fixer(text)
    if not changed:
        return text
    records.append(
        RepairRecord(
            repair_id=repair_id(len(records) + 1),
            doc_id=segment.doc_id,
            segment_id=segment.segment_id,
            repair_type=repair_type,
            original=text,
            fixed=fixed,
            reason=reason,
            confidence=Confidence.HIGH,
        )
    )
    segment.repair_count += 1
    if segment.action == SegmentAction.KEEP:
        segment.action = SegmentAction.REPAIR
    return fixed
