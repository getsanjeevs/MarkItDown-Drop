"""Thin wrapper around Microsoft's markitdown."""
from dataclasses import dataclass
from pathlib import Path

from markitdown import MarkItDown

_md = None


def _engine() -> MarkItDown:
    # Created lazily: construction is slow and the GUI should open instantly.
    global _md
    if _md is None:
        _md = MarkItDown(enable_plugins=False)
    return _md


@dataclass
class ConversionResult:
    source: Path
    markdown: str = ""
    title: str | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def convert_file(path: str | Path) -> ConversionResult:
    """Convert one file to raw Markdown. Never raises; errors are returned."""
    path = Path(path)
    try:
        result = _engine().convert(str(path))
        return ConversionResult(path, result.markdown, getattr(result, "title", None))
    except Exception as exc:  # markitdown raises many exception types
        return ConversionResult(path, error=f"{type(exc).__name__}: {exc}")
