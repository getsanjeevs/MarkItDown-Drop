"""YAML front matter for converted documents."""
import json
import re
from datetime import datetime
from pathlib import Path

from app import __version__
from app.verify import tokens


def _q(value: str) -> str:
    # A JSON string is also a valid YAML double-quoted string.
    return json.dumps(value, ensure_ascii=False)


def guess_title(markdown: str, source: Path, converter_title: str | None) -> str:
    if converter_title and converter_title.strip():
        return converter_title.strip()
    m = re.search(r"^#{1,6}\s+(.+?)\s*$", markdown, re.MULTILINE)
    return m.group(1) if m else source.stem


def build_front_matter(markdown: str, source: Path, converter_title: str | None = None) -> str:
    fields = [
        ("title", _q(guess_title(markdown, source, converter_title))),
        ("source_file", _q(source.name)),
        ("source_type", _q(source.suffix.lstrip(".").lower() or "unknown")),
        ("converted_at", _q(datetime.now().astimezone().isoformat(timespec="seconds"))),
        ("word_count", str(len(tokens(markdown)))),
        ("converter", _q(f"markitdown-drop {__version__}")),
    ]
    body = "\n".join(f"{k}: {v}" for k, v in fields)
    return f"---\n{body}\n---\n\n"
