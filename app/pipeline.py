"""Convert -> format -> verify -> write. Used by the GUI and by tests."""
from dataclasses import dataclass, field
from pathlib import Path

from app.converter import convert_file
from app.formatter import FormatOptions, format_markdown
from app.frontmatter import build_front_matter
from app.verify import content_preserved

# Used only when expanding dropped folders; explicitly dropped files are always tried.
SUPPORTED_EXTENSIONS = {
    ".docx", ".pptx", ".xlsx", ".xls", ".pdf", ".html", ".htm", ".csv",
    ".json", ".xml", ".txt", ".msg", ".epub", ".zip",
}


@dataclass
class Options:
    tidy: bool = True
    front_matter: bool = True
    output_dir: Path | None = None  # None -> "markdown" folder beside each source
    format: FormatOptions = field(default_factory=FormatOptions)


@dataclass
class Outcome:
    source: Path
    output: Path | None = None
    error: str | None = None
    warning: str | None = None


def expand_paths(paths: list[str | Path]) -> list[Path]:
    """Files stay as they are; folders are searched recursively."""
    files: list[Path] = []
    for p in map(Path, paths):
        if p.is_dir():
            files += sorted(
                f for f in p.rglob("*")
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
                and "markdown" not in f.relative_to(p).parts[:-1]
            )
        elif p.is_file():
            files.append(p)
    return files


def _output_path(source: Path, out_dir: Path, used: set[Path]) -> Path:
    target = out_dir / f"{source.stem}.md"
    if target in used:  # e.g. report.docx and report.pdf in the same batch
        target = out_dir / f"{source.stem}_{source.suffix.lstrip('.')}.md"
    used.add(target)
    return target


def process_file(source: Path, options: Options, used: set[Path] | None = None) -> Outcome:
    used = used if used is not None else set()
    result = convert_file(source)
    if not result.ok:
        return Outcome(source, error=result.error)

    raw = result.markdown
    text, warning = raw, None
    if options.tidy:
        formatted = format_markdown(raw, options.format)
        if content_preserved(raw, formatted):
            text = formatted
        else:
            warning = "Tidy-up skipped: it would have changed the content, so the original conversion was saved."
    if options.front_matter:
        text = build_front_matter(text, source, result.title) + text
    if not text.endswith("\n"):
        text += "\n"

    out_dir = options.output_dir or source.parent / "markdown"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        target = _output_path(source, out_dir, used)
        target.write_text(text, encoding="utf-8")
    except OSError as exc:
        return Outcome(source, error=f"Could not write output: {exc}")
    return Outcome(source, output=target, warning=warning)
