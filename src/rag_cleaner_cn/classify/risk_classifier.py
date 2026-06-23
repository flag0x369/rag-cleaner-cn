from __future__ import annotations

import re

from rag_cleaner_cn.core.enums import RiskTag


def classify_risks(text: str) -> tuple[list[RiskTag], str | None]:
    """Detect issues that should be surfaced for human review instead of guessed."""

    risk_tags: list[RiskTag] = []
    reasons: list[str] = []
    if re.search(
        r"(大家看这里|看这里|这个图左边|这个图右边|图里|表里面|圈出来|如下图|见下图)", text
    ):
        risk_tags.append(RiskTag.MEDIA_DEPENDENCY)
        reasons.append("依赖图片、视频画面或演示位置")
    if re.search(r"(如下表|见下表|表格如下)", text):
        risk_tags.append(RiskTag.TABLE_LOSS)
        reasons.append("疑似表格内容缺失")
    if re.search(r"(如下图|见下图)", text):
        risk_tags.append(RiskTag.IMAGE_LOSS)
        reasons.append("疑似图片内容缺失")
    if re.search(r"(私城|增张)", text) and not re.search(r"(私域|增长|运营|流量)", text):
        risk_tags.append(RiskTag.POSSIBLE_ASR_ERROR)
        reasons.append("疑似 ASR 错词但上下文不足")
    if text.endswith(("这个", "那个", "这里", "如下")):
        risk_tags.append(RiskTag.SEMANTIC_BREAK)
        reasons.append("语义疑似断裂或缺少后文")
    return risk_tags, "；".join(reasons) if reasons else None
