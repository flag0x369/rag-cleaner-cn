from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_text(text: str) -> str:
    """Return a hex SHA-256 hash for text."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    """Return a hex SHA-256 hash for a file without loading it all into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_doc_id(source_identifier: str) -> str:
    """Build a deterministic document ID from path, URL, hash, or text fingerprint."""

    return f"doc_{hashlib.sha256(source_identifier.encode('utf-8')).hexdigest()[:12]}"
