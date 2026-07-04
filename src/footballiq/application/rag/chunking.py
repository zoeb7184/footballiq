"""Heading-aware Markdown chunker (rag-design §4).

Splits a document along its heading structure so each chunk carries a section
trail (used for citation), then further splits over-long sections on paragraph
boundaries to stay near the embedding budget. Pure and deterministic — same
text in, same chunks out.
"""

from __future__ import annotations

import hashlib
import re

from footballiq.application.rag.ports import Chunk

_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
# ~300-500 token target; approximate with words (roughly 0.75 words/token).
_MAX_WORDS = 350


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _chunk_id(source_path: str, section: str, ordinal: int) -> str:
    # sha1 as a short stable id (not a security digest); collisions negligible.
    raw = f"{source_path}::{section}::{ordinal}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def _split_paragraphs(body: str) -> list[str]:
    """Group paragraphs into blocks that stay under the word budget."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    blocks: list[str] = []
    current: list[str] = []
    words = 0
    for para in paras:
        pw = len(para.split())
        if current and words + pw > _MAX_WORDS:
            blocks.append("\n\n".join(current))
            current, words = [], 0
        current.append(para)
        words += pw
    if current:
        blocks.append("\n\n".join(current))
    return blocks


def chunk_markdown(source_path: str, source_type: str, text: str) -> list[Chunk]:
    """Split Markdown into heading-scoped, budget-bounded chunks."""
    trail: list[tuple[int, str]] = []
    buffer: list[str] = []
    chunks: list[Chunk] = []

    def flush() -> None:
        body = "\n".join(buffer).strip()
        buffer.clear()
        if not body:
            return
        section = " > ".join(title for _, title in trail) or source_path
        for ordinal, block in enumerate(_split_paragraphs(body)):
            chunks.append(Chunk(
                chunk_id=_chunk_id(source_path, section, ordinal),
                source_path=source_path,
                source_type=source_type,
                section=section,
                content=block,
                content_hash=_sha256(block),
            ))

    for line in text.splitlines():
        m = _HEADING.match(line)
        if m:
            flush()
            level = len(m.group(1))
            while trail and trail[-1][0] >= level:
                trail.pop()
            trail.append((level, m.group(2)))
        else:
            buffer.append(line)
    flush()
    return chunks
