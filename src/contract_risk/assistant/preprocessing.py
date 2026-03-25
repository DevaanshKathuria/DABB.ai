"""Retrieval-oriented preprocessing for contracts and legal guidance."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from contract_risk.features.segmentation import clean_text, segment_clauses

SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")

CLAUSE_TAG_RULES: dict[str, tuple[str, ...]] = {
    "termination": ("terminate", "termination", "cancel", "breach"),
    "liability": ("liability", "indemn", "damages", "loss"),
    "confidentiality": ("confidential", "non-disclosure", "nda", "secret"),
    "payment": ("payment", "invoice", "fee", "late fee", "consideration"),
    "arbitration": ("arbitration", "mediation", "dispute resolution", "forum"),
    "force majeure": ("force majeure", "act of god", "pandemic", "flood", "war"),
    "governing law": ("governing law", "jurisdiction", "venue", "state law"),
}


@dataclass(frozen=True)
class RetrievalChunk:
    """A retrieval-ready passage with metadata tags."""

    chunk_id: str
    source_id: str
    clause_index: int
    chunk_index: int
    text: str
    tags: tuple[str, ...] = field(default_factory=tuple)
    char_start: int = 0
    char_end: int = 0

    def as_document(self) -> str:
        """Return text enriched with metadata for retrieval indexing."""
        tag_text = ", ".join(self.tags)
        return f"{self.text}\nTags: {tag_text}" if tag_text else self.text


def infer_clause_tags(text: str) -> tuple[str, ...]:
    """Infer lightweight metadata tags from clause wording."""
    normalized = text.lower()
    tags: list[str] = []
    for tag, keywords in CLAUSE_TAG_RULES.items():
        if any(keyword in normalized for keyword in keywords):
            tags.append(tag)
    return tuple(tags)


def _split_clause_text(text: str, max_chars: int) -> list[str]:
    """Split a long clause without breaking sentence flow abruptly."""
    if len(text) <= max_chars:
        return [text.strip()]

    sentences = [segment.strip() for segment in SENTENCE_PATTERN.split(text) if segment.strip()]
    if not sentences:
        return [text[i : i + max_chars].strip() for i in range(0, len(text), max_chars)]

    chunks: list[str] = []
    current: list[str] = []

    for sentence in sentences:
        candidate = " ".join(current + [sentence]).strip()
        if current and len(candidate) > max_chars:
            chunks.append(" ".join(current).strip())
            current = [sentence]
        else:
            current.append(sentence)

    if current:
        chunks.append(" ".join(current).strip())

    return [chunk for chunk in chunks if chunk]


def build_retrieval_chunks(
    text: str,
    *,
    source_id: str = "contract",
    max_clause_chars: int = 450,
) -> list[RetrievalChunk]:
    """Create clean, metadata-rich chunks for vector retrieval."""
    normalized = clean_text(text)
    if not normalized:
        return []

    clauses = segment_clauses(normalized)
    chunks: list[RetrievalChunk] = []

    for clause_index, clause in enumerate(clauses, start=1):
        clause_tags = infer_clause_tags(clause)
        clause_parts = _split_clause_text(clause, max_chars=max_clause_chars)

        cursor = 0
        for chunk_index, part in enumerate(clause_parts, start=1):
            part = part.strip()
            if not part:
                continue

            start = cursor
            end = min(len(clause), start + len(part))
            chunks.append(
                RetrievalChunk(
                    chunk_id=f"{source_id}-c{clause_index:03d}-p{chunk_index:02d}",
                    source_id=source_id,
                    clause_index=clause_index,
                    chunk_index=chunk_index,
                    text=part,
                    tags=clause_tags,
                    char_start=start,
                    char_end=end,
                )
            )
            cursor = end + 1

    return chunks
