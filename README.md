# MarkItDown Drop

Drag and drop documents onto a window and get clean Markdown files back. No installation, no Python, no command line.

Built on Microsoft's open-source [markitdown](https://github.com/microsoft/markitdown). On top of the plain conversion it can:

- **Tidy the Markdown** (consistent headings, bullets, table alignment, spacing, re-joined hard-wrapped lines) without removing any content. Every file is checked: if tidying would change a single word, the untouched conversion is saved instead and you get a warning.
- **Add YAML front matter** (title, source file, type, date, word count) so the files are ready for note apps, wikis and AI/RAG tools.

Supported inputs: Word, PowerPoint, Excel, PDF, HTML, CSV, JSON, XML, text, Outlook .msg, EPUB, ZIP.

## For users (Windows)
1. Download `MarkItDownDrop.exe` from the Releases page.
2. Double-click it, wait for "Drag & drop files or folders here".
3. Drop files or folders. Results appear in a `markdown` folder next to each file (or the folder you choose).

Windows may show "Windows protected your PC" because the app is not code-signed yet: click **More info → Run anyway**.

## For developers
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest        # run tests
.\.venv\Scripts\python.exe -m app.main      # run the app
.\build.ps1                                 # build dist\MarkItDownDrop.exe
```

Layout: `app/converter.py` (markitdown wrapper), `app/formatter.py` (tidy rules), `app/frontmatter.py`, `app/verify.py` (content-preservation check), `app/pipeline.py` (convert → tidy → verify → write), `app/gui.py`.

## License
MIT. markitdown is also MIT-licensed.
