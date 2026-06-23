def tail_overlap(text: str, overlap_chars: int) -> str:
    """Return a tail overlap string for long fallback chunks."""

    if overlap_chars <= 0:
        return ""
    return text[-overlap_chars:]
