from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel


def write_jsonl(path: Path, rows: Iterable[BaseModel | dict]) -> None:
    """Write rows as UTF-8 JSONL with Chinese preserved."""

    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            data = row.model_dump(mode="json") if isinstance(row, BaseModel) else row
            handle.write(json.dumps(data, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
