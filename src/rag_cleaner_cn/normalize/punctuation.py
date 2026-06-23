import re

_FULLWIDTH_MAP = str.maketrans(
    {
        "，": "，",
        "。": "。",
        "？": "？",
        "！": "！",
        "；": "；",
        "：": "：",
        "（": "（",
        "）": "）",
    }
)


def normalize_punctuation(text: str) -> str:
    """Normalize repeated punctuation without rewriting style."""

    text = text.translate(_FULLWIDTH_MAP)
    text = re.sub(r"[。]{2,}", "。", text)
    text = re.sub(r"[，]{2,}", "，", text)
    text = re.sub(r"[!！]{2,}", "！", text)
    text = re.sub(r"[?？]{2,}", "？", text)
    return text
