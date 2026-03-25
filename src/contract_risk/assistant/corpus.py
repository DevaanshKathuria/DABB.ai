"""Load the normalized legal guidance corpus used by the assistant layer."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LegalGuidanceRecord:
    """Normalized legal guidance passage for retrieval."""

    id: str
    title: str
    source_name: str
    source_url: str
    jurisdiction: str
    topic: str
    clause_tags: tuple[str, ...]
    passage: str
    risk_signal: str

    @property
    def search_text(self) -> str:
        """Return a retrieval-friendly text representation."""
        tags = ", ".join(self.clause_tags)
        return f"{self.title}. {self.passage} Tags: {tags}. Signal: {self.risk_signal}"


def _normalize_record(payload: dict[str, Any]) -> LegalGuidanceRecord:
    """Convert a raw JSON record into a typed data object."""
    return LegalGuidanceRecord(
        id=str(payload["id"]).strip(),
        title=str(payload["title"]).strip(),
        source_name=str(payload["source_name"]).strip(),
        source_url=str(payload["source_url"]).strip(),
        jurisdiction=str(payload.get("jurisdiction", "US")).strip(),
        topic=str(payload.get("topic", "general")).strip(),
        clause_tags=tuple(str(item).strip() for item in payload.get("clause_tags", [])),
        passage=str(payload["passage"]).strip(),
        risk_signal=str(payload["risk_signal"]).strip(),
    )


def load_legal_guidance_corpus(path: str | Path | None = None) -> list[LegalGuidanceRecord]:
    """Load the bundled legal guidance corpus from JSON."""
    default_path = Path(__file__).resolve().parents[3] / "data" / "legal_guidelines" / "corpus.json"
    corpus_path = Path(path) if path else default_path
    payload = json.loads(corpus_path.read_text(encoding="utf-8"))
    records = payload.get("records", payload)
    return [_normalize_record(record) for record in records]
