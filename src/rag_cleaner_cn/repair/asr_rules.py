from __future__ import annotations

_HIGH_CONFIDENCE_DOMAIN_TERMS = {
    "乔哈里创",
    "囚禁已知",
    "SPN",
    "BNT",
    "痛苦恋",
    "线刃",
    "销 售",
    "1 00%",
}


def apply_asr_homophone_rules(
    text: str, candidates: dict[str, str], context: str
) -> tuple[str, bool]:
    """Apply homophone candidates only when local context gives high confidence."""

    fixed = text
    for wrong, right in candidates.items():
        if wrong not in fixed:
            continue
        if _has_high_confidence_context(wrong, right, fixed, context):
            fixed = fixed.replace(wrong, right)
    return fixed, fixed != text


def _has_high_confidence_context(wrong: str, right: str, text: str, context: str) -> bool:
    combined = f"{text}\n{context}"
    if wrong in _HIGH_CONFIDENCE_DOMAIN_TERMS:
        return True
    if wrong == "私城" and ("流量" in text or "私域" in combined or "运营" in combined):
        return True
    if wrong == "增张" and ("增长" in combined or "用户" in combined or "转化" in combined):
        return True
    return right in combined
