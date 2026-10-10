from pathlib import Path

from app.pipeline import Options, expand_paths, process_file

SAMPLES = Path(__file__).parent.parent / "samples"


def test_html_sample_end_to_end(tmp_path):
    out = process_file(SAMPLES / "sample.html", Options(output_dir=tmp_path))
    assert out.error is None and out.warning is None
    text = out.output.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "## Highlights" in text  # H3 promoted to H2
    assert "Quarterly Report" in text and "250" in text


def test_corrupt_file_reports_error_without_raising(tmp_path):
    bad = tmp_path / "broken.bin"
    bad.write_bytes(bytes(range(256)) * 20)
    out = process_file(bad, Options(output_dir=tmp_path / "o"))
    assert out.error and out.output is None


def test_name_collision_in_one_batch(tmp_path):
    (tmp_path / "a.txt").write_text("alpha")
    (tmp_path / "a.csv").write_text("x,y\n1,2\n")
    used: set = set()
    o = Options(output_dir=tmp_path / "o")
    r1 = process_file(tmp_path / "a.txt", o, used)
    r2 = process_file(tmp_path / "a.csv", o, used)
    assert r1.output != r2.output


def test_expand_folder_filters_extensions(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "b.exe").write_bytes(b"x")
    assert [p.name for p in expand_paths([tmp_path])] == ["a.txt"]
