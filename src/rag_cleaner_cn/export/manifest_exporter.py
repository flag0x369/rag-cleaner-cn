from __future__ import annotations

import json
from pathlib import Path

from rag_cleaner_cn.core.models import Manifest


def write_manifest(path: Path, manifest: Manifest) -> None:
    path.write_text(
        json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
