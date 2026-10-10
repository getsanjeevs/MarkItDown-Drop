# markitdown-drop

Windows drag-and-drop utility on top of Microsoft `markitdown`: converts documents to Markdown, then tidies it and adds YAML front matter without losing content. Open source (MIT). Target users are non-technical; ship as a single portable .exe.

## Stack
- Python 3.12, venv in `.venv` (activate: `.\.venv\Scripts\Activate.ps1`; or call `.\.venv\Scripts\python.exe` directly)
- GUI: customtkinter + tkinterdnd2. Packaging: PyInstaller.
- Tests: `.\.venv\Scripts\python.exe -m pytest`

## Layout
- `app/converter.py` markitdown wrapper (never raises)
- `app/formatter.py` deterministic cleanup rules (pure functions)
- `app/frontmatter.py` YAML header
- `app/verify.py` content-preservation check: formatted output must contain every word of the raw output, else fall back to raw
- `app/gui.py`, `app/main.py` UI
- `tests/`, `samples/`

## Conventions
- Core rule: never remove or alter content. Formatting changes whitespace/structure only; `verify.py` enforces it.
- The user's background is C#, not Python: keep code simple and typed, and explain Python idioms in C# terms when asked.
- Windows/PowerShell environment; PATH may need refreshing in a new shell session.
