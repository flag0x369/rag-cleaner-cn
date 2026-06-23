import re


def strip_html_residue(text: str) -> str:
    """Remove obvious HTML tag residue while keeping textual content."""

    return re.sub(r"</?[^>\n]+>", "", text)


def markdown_heading_level(text: str) -> int | None:
    match = re.match(r"^(#{1,6})\s+(.+)$", text.strip())
    if not match:
        return None
    return len(match.group(1))


def markdown_heading_text(text: str) -> str:
    return re.sub(r"^#{1,6}\s+", "", text.strip()).strip()
