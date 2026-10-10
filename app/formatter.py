"""Deterministic Markdown cleanup rules.

Every rule only changes whitespace, heading depth, list markers or table
padding. No words are added or removed; app/verify.py double-checks that.
"""
import re
from dataclasses import dataclass

_FENCE = re.compile(r"^\s{0,3}(```|~~~)")
_HEADING = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t#]*$")
_HR = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
_BULLET = re.compile(r"^(\s*)[*+](\s+\S)")
_SEPARATOR_CELL = re.compile(r"^:?-+:?$")
_SENTENCE_END = re.compile(r"[.!?:;]$")


@dataclass
class FormatOptions:
    normalize_whitespace: bool = True
    fix_headings: bool = True
    normalize_bullets: bool = True
    align_tables: bool = True
    unwrap_paragraphs: bool = True


def format_markdown(text: str, options: FormatOptions | None = None) -> str:
    """Apply all enabled rules in a fixed order."""
    o = options or FormatOptions()
    if o.normalize_whitespace:
        text = normalize_whitespace(text)
    if o.fix_headings:
        text = fix_headings(text)
    if o.normalize_bullets:
        text = normalize_bullets(text)
    if o.align_tables:
        text = align_tables(text)
    if o.unwrap_paragraphs:
        text = unwrap_paragraphs(text)
    if o.normalize_whitespace:
        text = normalize_whitespace(text)
    return text


def _with_fence_state(lines: list[str]):
    """Yield (line, in_code) where fence lines themselves count as code."""
    in_code = False
    marker = ""
    for line in lines:
        m = _FENCE.match(line)
        if m and not in_code:
            in_code, marker = True, m.group(1)
            yield line, True
        elif in_code and line.strip().startswith(marker):
            in_code = False
            yield line, True
        else:
            yield line, in_code


def _has_unclosed_fence(lines: list[str]) -> bool:
    open_ = False
    marker = ""
    for line in lines:
        m = _FENCE.match(line)
        if m and not open_:
            open_, marker = True, m.group(1)
        elif open_ and line.strip().startswith(marker):
            open_ = False
    return open_


def normalize_whitespace(text: str) -> str:
    """Unix newlines, no trailing spaces, max one blank line, blank lines around
    headings, closed code fences, single trailing newline."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    out: list[str] = []
    lines = text.split("\n")
    for line, code in _with_fence_state(lines):
        if code:
            out.append(line)
            continue
        line = line.rstrip()
        if line == "" and out and out[-1] == "":
            continue
        if _HEADING.match(line) and out and out[-1] != "":
            out.append("")
        if out and out[-1] != "" and _HEADING.match(out[-1]) and line != "":
            out.append("")
        out.append(line)
    if _has_unclosed_fence(lines):
        out.append("```")  # close an unterminated fence
    return "\n".join(out).strip("\n") + "\n"


def fix_headings(text: str) -> str:
    """Stop heading levels from skipping (H1 -> H3 becomes H1 -> H2), keeping
    sibling headings at the same level."""
    stack: list[tuple[int, int]] = []  # (original level, new level)
    out = []
    for line, code in _with_fence_state(text.split("\n")):
        m = None if code else _HEADING.match(line)
        if not m:
            out.append(line)
            continue
        orig = len(m.group(1))
        while stack and stack[-1][0] >= orig:
            stack.pop()
        new = min(stack[-1][1] + 1, 6) if stack else orig
        stack.append((orig, new))
        out.append(f"{'#' * new} {m.group(2)}".rstrip())
    return "\n".join(out)


def normalize_bullets(text: str) -> str:
    """Use '-' for every unordered list item."""
    out = []
    for line, code in _with_fence_state(text.split("\n")):
        if not code and not _HR.match(line):
            line = _BULLET.sub(r"\1-\2", line)
        out.append(line)
    return "\n".join(out)


def _split_row(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", body)]


def _is_table_line(line: str) -> bool:
    return line.lstrip().startswith("|") and line.count("|") >= 2


def _render_table(rows: list[list[str]]) -> list[str]:
    cols = max(len(r) for r in rows)
    rows = [r + [""] * (cols - len(r)) for r in rows]
    is_sep = len(rows) > 1 and all(_SEPARATOR_CELL.match(c) for c in rows[1])
    widths = [
        max(3, *(len(r[i]) for j, r in enumerate(rows) if not (is_sep and j == 1)))
        for i in range(cols)
    ]
    rendered = []
    for j, r in enumerate(rows):
        if is_sep and j == 1:
            cells = []
            for i, c in enumerate(r):
                left, right = c.startswith(":"), c.endswith(":")
                dashes = "-" * (widths[i] - left - right)
                cells.append(f"{':' if left else ''}{dashes}{':' if right else ''}")
        else:
            cells = [c.ljust(widths[i]) for i, c in enumerate(r)]
        rendered.append("| " + " | ".join(cells) + " |")
    return rendered


def align_tables(text: str) -> str:
    """Pad table columns and make sure tables are surrounded by blank lines."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    in_code = False
    marks = [code for _, code in _with_fence_state(lines)]
    while i < len(lines):
        if not marks[i] and _is_table_line(lines[i]):
            j = i
            while j < len(lines) and not marks[j] and _is_table_line(lines[j]):
                j += 1
            if out and out[-1] != "":
                out.append("")
            out.extend(_render_table([_split_row(l) for l in lines[i:j]]))
            if j < len(lines) and lines[j] != "":
                out.append("")
            i = j
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out)


def _is_plain_paragraph_line(line: str) -> bool:
    s = line.strip()
    if not s or line.startswith(("    ", "\t")):
        return False
    if s[0] in "#>|-*+<`~" or _HR.match(line) or _FENCE.match(line):
        return False
    if re.match(r"^\d+[.)]\s", s):
        return False
    return True


def unwrap_paragraphs(text: str) -> str:
    """Join hard-wrapped lines (typical for PDFs) when it is clearly the same
    sentence: line does not end in punctuation and the next starts lowercase."""
    out: list[str] = []
    for line, code in _with_fence_state(text.split("\n")):
        if (
            not code
            and out
            and _is_plain_paragraph_line(line)
            and _is_plain_paragraph_line(out[-1])
            and not _SENTENCE_END.search(out[-1].rstrip())
            and line.lstrip()[0].islower()
        ):
            out[-1] = out[-1].rstrip() + " " + line.lstrip()
        else:
            out.append(line)
    return "\n".join(out)
