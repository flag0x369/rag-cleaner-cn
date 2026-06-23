import re

from rag_cleaner_cn.normalize.markdown import markdown_heading_level, markdown_heading_text


def is_heading(text: str) -> bool:
    stripped = text.strip()
    if markdown_heading_level(stripped):
        return True
    return bool(
        re.match(
            r"^(第[一二三四五六七八九十百0-9]+[章节部分讲]|[一二三四五六七八九十]+、).{1,40}$",
            stripped,
        )
    )


def heading_level(text: str) -> int:
    level = markdown_heading_level(text)
    if level:
        return level
    stripped = text.strip()
    if stripped.startswith("第"):
        return 2
    return 3


def heading_title(text: str) -> str:
    if markdown_heading_level(text):
        return markdown_heading_text(text)
    return re.sub(r"^[一二三四五六七八九十]+、", "", text.strip()).strip()
