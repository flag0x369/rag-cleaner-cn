from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from rag_cleaner_cn.core.enums import SourceType
from rag_cleaner_cn.core.models import SourceDocument
from rag_cleaner_cn.ingest.base import build_source_document


class HtmlLoader:
    supported_suffixes = {".html", ".htm"}

    def load(self, path: Path, source_type: SourceType | None = None) -> SourceDocument:
        html = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        title = soup.title.get_text(strip=True) if soup.title else path.stem
        lines: list[str] = []
        for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote"]):
            text = element.get_text(" ", strip=True)
            if not text:
                continue
            if element.name and element.name.startswith("h"):
                level = int(element.name[1])
                lines.append(f"{'#' * level} {text}")
            elif element.name == "li":
                lines.append(f"- {text}")
            else:
                lines.append(text)
        raw_text = "\n\n".join(lines) if lines else soup.get_text("\n", strip=True)
        return build_source_document(
            raw_text,
            path=path,
            source_type=source_type or SourceType.WEB_ARTICLE,
            title=title,
        )
