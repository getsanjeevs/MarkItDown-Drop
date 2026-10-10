"""Content-preservation check.

Markdown syntax contains almost no letters or digits, so comparing the ordered
sequence of word tokens before and after formatting proves that no text was
removed, added, changed or reordered.
"""
import re

_WORD = re.compile(r"\w+", re.UNICODE)


def tokens(markdown: str) -> list[str]:
    return _WORD.findall(markdown)


def content_preserved(raw: str, formatted: str) -> bool:
    return tokens(raw) == tokens(formatted)
