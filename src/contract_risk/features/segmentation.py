"""Clause segmentation utilities for legal text."""

from __future__ import annotations

import re
from typing import List

NUMBERED_PATTERN = re.compile(r"^\s*(?:\d+(?:\.\d+)*\s+|\([a-z]\)\s+)", re.IGNORECASE)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")


def clean_text(text: str) -> str:
    """Normalize whitespace while preserving line structure."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\t+", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _merge_tiny_fragments(chunks: List[str], min_chars: int = 30) -> List[str]:
    """Merge tiny chunks into neighboring chunks for readability."""
    if not chunks:
        return []

    merged: List[str] = []
    for chunk in chunks:
        current = chunk.strip()
        if not current:
            continue

        if merged and len(current) < min_chars:
            merged[-1] = f"{merged[-1]} {current}".strip()
        else:
            merged.append(current)

    if len(merged) > 1 and len(merged[0]) < min_chars:
        merged[1] = f"{merged[0]} {merged[1]}".strip()
        merged = merged[1:]

    return merged


def _fallback_sentence_chunking(text: str, chunk_size: int = 2) -> List[str]:
    """Fallback segmentation using sentence grouping."""
    sentences = [s.strip() for s in SENTENCE_SPLIT_PATTERN.split(text) if s.strip()]
    if not sentences:
        return [text.strip()] if text.strip() else []

    grouped: List[str] = []
    for i in range(0, len(sentences), chunk_size):
        grouped.append(" ".join(sentences[i : i + chunk_size]))
    return grouped


def segment_clauses(text: str, min_chars: int = 30) -> List[str]:
    """Split legal text into likely clause units.

    Strategy:
    1. Detect numbered/bulleted clause starts.
    2. Merge tiny fragments.
    3. Fallback to sentence chunking when no structure exists.
    """
    normalized = clean_text(text)
    if not normalized:
        return []

    lines = [line.strip() for line in normalized.split("\n") if line.strip()]

    clauses: List[str] = []
    current: List[str] = []

    for line in lines:
        if NUMBERED_PATTERN.match(line) and current:
            clauses.append(" ".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        clauses.append(" ".join(current).strip())

    structured_count = sum(1 for line in lines if NUMBERED_PATTERN.match(line))
    if structured_count == 0 or len(clauses) <= 1:
        clauses = _fallback_sentence_chunking(normalized)

    return _merge_tiny_fragments(clauses, min_chars=min_chars)
