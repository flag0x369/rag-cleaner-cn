import re


def estimate_token_count(text: str) -> int:
    """Approximate token count with a conservative CJK-friendly heuristic."""

    cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    non_cjk_tokens = len(re.findall(r"[A-Za-z0-9_]+", text))
    punctuation = len(re.findall(r"[，。！？；：,.!?;:]", text))
    return cjk_chars + non_cjk_tokens + punctuation
