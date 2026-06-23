from __future__ import annotations

import re
from typing import Any

from rag_cleaner_cn.core.enums import NoiseType

_KNOWLEDGE_SIGNALS = (
    "不是",
    "而是",
    "因为",
    "导致",
    "关键",
    "机制",
    "方法",
    "方法论",
    "策略",
    "案例",
    "定义",
    "原理",
    "步骤",
    "增长",
    "转化",
    "用户",
    "运营",
    "私域",
    "企业微信",
    "承接",
    "链路",
    "触点",
    "动作",
    "闭环",
    "交付",
    "筛选",
    "分析",
    "判断",
    "建联",
    "触达",
)


def classify_noise(text: str, rules: dict[str, Any]) -> tuple[NoiseType, str | None]:
    """Return a noise type only when the whole paragraph is low-value noise."""

    stripped = text.strip()
    if not stripped:
        return NoiseType.EMPTY, "空段落"
    if re.fullmatch(r"#+", stripped):
        return NoiseType.DECORATION, "空标题占位"
    if _is_platform_unavailable_notice(stripped):
        return NoiseType.FOOTER, "平台不可查看提示"
    if re.fullmatch(r"https?://\S+", stripped):
        return NoiseType.URL_ONLY, "纯 URL 行"
    if re.fullmatch(r"[\-—_=*#·\s]{3,}", stripped):
        return NoiseType.DECORATION, "纯装饰符号行"
    if _is_filler_only(stripped, rules):
        return NoiseType.TRANSCRIPT_ARTIFACT, "纯语气填充词，无正文知识价值"
    if _is_classroom_noise(stripped, rules):
        return NoiseType.TRANSCRIPT_ARTIFACT, "纯课堂互动噪声"
    if _matches_any(stripped, rules.get("image_placeholder_patterns", [])):
        return NoiseType.IMAGE_PLACEHOLDER, "纯图片占位"
    if _matches_any(stripped, rules.get("transcript_artifact_patterns", [])):
        return NoiseType.TRANSCRIPT_ARTIFACT, "字幕或转写工具残留"
    if _matches_any(stripped, rules.get("footer_patterns", [])) and _is_short_noise(
        stripped, rules
    ):
        return NoiseType.FOOTER, "纯页脚或版权提示"
    if _is_pure_wechat_noise(stripped, rules):
        return NoiseType.MARKETING, "纯互动或运营转化提示"
    if _is_strong_marketing_footer(stripped, rules):
        return NoiseType.MARKETING, "纯运营转化，无正文知识价值"
    if _is_pure_marketing(stripped, rules):
        return NoiseType.MARKETING, "纯运营转化，无正文知识价值"
    return NoiseType.NONE, None


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _is_short_noise(text: str, rules: dict[str, Any]) -> bool:
    return len(text) <= _rule_int(rules, "short_noise_max_chars", 80) and not any(
        signal in text for signal in _KNOWLEDGE_SIGNALS
    )


def _is_pure_wechat_noise(text: str, rules: dict[str, Any]) -> bool:
    if not _is_short_noise(text, rules):
        return False
    patterns = rules.get("wechat_noise_patterns", [])
    hits = sum(1 for pattern in patterns if re.search(pattern, text))
    return hits >= 2 or bool(
        re.fullmatch(r"(点赞|在看|转发|分享|关注公众号|分享给朋友)[、，。\s]+", text)
    )


def _is_pure_marketing(text: str, rules: dict[str, Any]) -> bool:
    if not _is_short_noise(text, rules):
        return False
    if _is_sales_action_context(text):
        return False
    return _matches_any(text, rules.get("marketing_patterns", []))


def _is_strong_marketing_footer(text: str, rules: dict[str, Any]) -> bool:
    if len(text) > _rule_int(rules, "strong_marketing_max_chars", 140):
        return False
    return _matches_any(text, rules.get("strong_marketing_patterns", []))


def _is_filler_only(text: str, rules: dict[str, Any]) -> bool:
    normalized = re.sub(r"[，,。！？!?\s]+", "", text)
    filler_words = set(rules.get("filler_words", []))
    if normalized in filler_words:
        return True
    particle_stripped = re.sub(r"[啊呃嗯额]+", "", normalized)
    return not particle_stripped or particle_stripped in filler_words


def _is_classroom_noise(text: str, rules: dict[str, Any]) -> bool:
    if not _is_short_noise(text, rules):
        return False
    return _matches_any(text, rules.get("classroom_noise_patterns", []))


def _is_sales_action_context(text: str) -> bool:
    """Keep sales tactics that mention contact channels without conversion intent."""

    if "客户" not in text:
        return False
    if not re.search(r"(微信|电话|联系方式|建联|触达|拜访)", text):
        return False
    conversion_terms = (
        "领取",
        "扫码",
        "二维码",
        "回复666",
        "关注公众号",
        "关注我",
        "关注本号",
        "点个关注",
        "添加我",
        "加我",
        "个人微信",
        "报名",
        "预约",
        "优惠",
        "课程",
    )
    return not any(term in text for term in conversion_terms)


def _is_platform_unavailable_notice(text: str) -> bool:
    return "此内容因违规无法查看" in text and (
        "微信公众平台运营中心" in text or "查看对应规则" in text
    )


def _rule_int(rules: dict[str, Any], key: str, default: int) -> int:
    try:
        value = int(rules.get(key, default))
    except (TypeError, ValueError):
        return default
    return max(0, value)
