import re

_ENDING_PUNCT = "。！？!?；;：:）)]】》\"'"


def normalize_whitespace(text: str) -> str:
    """Normalize line endings, trim spaces, and join obvious CJK broken lines."""

    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\ufeff", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    joined: list[str] = []
    for line in lines:
        if not line:
            if joined and joined[-1] != "":
                joined.append("")
            continue
        if _should_join_with_previous(joined[-1] if joined else "", line):
            joined[-1] = f"{joined[-1]}{line}"
        else:
            joined.append(line)
    normalized = "\n".join(joined)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _should_join_with_previous(previous: str, current: str) -> bool:
    if not previous or previous == "":
        return False
    if previous.startswith("#") or current.startswith("#"):
        return False
    if previous.endswith(_ENDING_PUNCT):
        return False
    if re.match(r"^[-*+]\s+", current) or re.match(r"^\d+[.、]\s*", current):
        return False
    return bool(re.search(r"[\u4e00-\u9fff]$", previous) and re.match(r"^[\u4e00-\u9fff]", current))
