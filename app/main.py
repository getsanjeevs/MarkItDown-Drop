import sys


def _selftest(path: str) -> int:
    """Headless check used to verify a packaged build: `MarkItDownDrop.exe --selftest file`."""
    from pathlib import Path

    from app.pipeline import Options, process_file

    result = process_file(Path(path), Options())
    report = result.error or f"OK -> {result.output}"
    (Path(path).parent / "selftest.txt").write_text(report, encoding="utf-8")
    return 1 if result.error else 0


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--selftest":
        sys.exit(_selftest(sys.argv[2]))
    from app.gui import App

    App().mainloop()


if __name__ == "__main__":
    main()
