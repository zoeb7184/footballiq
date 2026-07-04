"""Markdown chunker tests (rag-design §4) — heading trails, budget, determinism."""

from footballiq.application.rag.chunking import _MAX_WORDS, chunk_markdown

_DOC = """# Title

Intro paragraph under the title.

## Section A

Body of A, one paragraph.

### Sub A1

Deep content here.

## Section B

Body of B.
"""


def test_sections_carry_heading_trail() -> None:
    chunks = chunk_markdown("docs/x.md", "doc", _DOC)
    sections = [c.section for c in chunks]
    assert "Title" in sections
    assert "Title > Section A" in sections
    assert "Title > Section A > Sub A1" in sections
    assert "Title > Section B" in sections


def test_metadata_and_ids_are_deterministic() -> None:
    a = chunk_markdown("docs/x.md", "doc", _DOC)
    b = chunk_markdown("docs/x.md", "doc", _DOC)
    assert [c.chunk_id for c in a] == [c.chunk_id for c in b]
    assert [c.content_hash for c in a] == [c.content_hash for c in b]
    assert all(c.source_type == "doc" and c.source_path == "docs/x.md" for c in a)


def test_empty_sections_dropped() -> None:
    chunks = chunk_markdown("docs/x.md", "doc", "# Only A Heading\n\n## Empty\n")
    # headings with no body produce no chunks
    assert all(c.content.strip() for c in chunks)


def test_long_section_splits_on_paragraph_budget() -> None:
    para = " ".join(["word"] * 200)
    big = f"# T\n\n## Big\n\n{para}\n\n{para}\n\n{para}\n"  # 600 words in one section
    chunks = [c for c in chunk_markdown("d.md", "doc", big)
              if c.section == "T > Big"]
    assert len(chunks) >= 2  # exceeded the single-chunk word budget
    assert all(len(c.content.split()) <= _MAX_WORDS + 200 for c in chunks)
