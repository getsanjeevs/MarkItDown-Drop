import yaml

from app.formatter import (
    align_tables, fix_headings, format_markdown, normalize_bullets,
    normalize_whitespace, unwrap_paragraphs,
)
from app.frontmatter import build_front_matter
from app.verify import content_preserved


def test_heading_jump_is_fixed_and_siblings_stay_equal():
    out = fix_headings("# A\n\n### B\n\n### C\n\n## D\n")
    assert out == "# A\n\n## B\n\n## C\n\n## D\n"


def test_headings_inside_code_fence_are_untouched():
    src = "# A\n\n```\n### not a heading\n```\n"
    assert fix_headings(src) == src


def test_bullets_normalized_but_not_rules_or_bold():
    out = normalize_bullets("* a\n+ b\n  * c\n\n* * *\n\n**bold** text\n")
    assert out == "- a\n- b\n  - c\n\n* * *\n\n**bold** text\n"


def test_whitespace_blank_lines_and_trailing_spaces():
    out = normalize_whitespace("Title   \r\n\r\n\r\n\r\ntext\r\n## H\r\nmore")
    assert out == "Title\n\ntext\n\n## H\n\nmore\n"


def test_unclosed_fence_is_closed():
    assert normalize_whitespace("```\ncode").endswith("```\n")


def test_table_alignment_and_blank_lines():
    out = align_tables("text\n| a | bb |\n|---|:-:|\n| long cell | x |\n")
    lines = out.split("\n")
    assert lines[1] == ""
    assert lines[2] == "| a         | bb  |"
    assert lines[3] == "| --------- | :-: |"
    assert lines[4] == "| long cell | x   |"


def test_escaped_pipe_stays_in_cell():
    out = align_tables("| a\\|b | c |\n| --- | --- |\n| 1 | 2 |\n")
    assert "a\\|b" in out


def test_unwrap_joins_only_clear_continuations():
    assert unwrap_paragraphs("this is a wrapped\nline here.\nNew sentence") == (
        "this is a wrapped line here.\nNew sentence"
    )
    assert unwrap_paragraphs("Heading text\nlower case") == "Heading text lower case"
    assert unwrap_paragraphs("- item\nlower") == "- item\nlower"


def test_full_pipeline_preserves_content():
    raw = (
        "# Title\r\n\r\n\r\n### Deep\r\n* one\r\n* two\r\n"
        "text that wraps\r\nacross lines.\r\n| a | b |\r\n|--|--|\r\n| 1 | 2 |\r\n"
    )
    out = format_markdown(raw)
    assert content_preserved(raw, out)
    assert "## Deep" in out and "- one" in out


def test_verify_detects_changes():
    assert not content_preserved("hello world", "hello")
    assert not content_preserved("a b", "b a")
    assert content_preserved("# hi\n\n* there", "## hi\n- there")


def test_front_matter_is_valid_yaml(tmp_path):
    src = tmp_path / 'My "Report".docx'
    fm = build_front_matter("# Real Title\n\nsome words", src)
    data = yaml.safe_load(fm.split("---")[1])
    assert data["title"] == "Real Title"
    assert data["source_file"] == 'My "Report".docx'
    assert data["source_type"] == "docx"
    assert data["word_count"] == 4
