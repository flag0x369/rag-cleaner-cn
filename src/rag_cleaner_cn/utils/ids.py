def segment_id(doc_id: str, index: int) -> str:
    return f"{doc_id}_seg_{index:04d}"


def chunk_id(doc_id: str, index: int) -> str:
    return f"{doc_id}_chunk_{index:04d}"


def repair_id(index: int) -> str:
    return f"repair_{index:04d}"


def review_id(index: int) -> str:
    return f"review_{index:04d}"
