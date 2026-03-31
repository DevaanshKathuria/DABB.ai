"""Free, local retrieval index for legal guidance passages."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping, Sequence
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from contract_risk.assistant.corpus import LegalGuidanceRecord

DEFAULT_KB_PATH = Path("models/legal_guidance_store.joblib")


@dataclass(frozen=True)
class RetrievalHit:
    """A single retrieved legal guidance passage."""

    record: LegalGuidanceRecord
    score: float


@dataclass(frozen=True)
class RetrievalQuery:
    """Structured retrieval request used by the assistant layer."""

    text: str
    predicted_type: str | None = None
    clause_tags: tuple[str, ...] = ()

    def as_text(self) -> str:
        """Render the query into retrieval text."""
        parts = [self.text.strip()]
        if self.predicted_type:
            parts.insert(0, self.predicted_type.strip())
        if self.clause_tags:
            parts.append(" ".join(tag.strip() for tag in self.clause_tags if tag.strip()))
        return " ".join(part for part in parts if part)


def _normalize_clause_tags(clause_tags: Sequence[str] | str | None) -> tuple[str, ...]:
    """Normalize clause tags from assorted assistant-layer inputs."""
    if clause_tags is None:
        return ()
    if isinstance(clause_tags, str):
        return tuple(tag.strip() for tag in clause_tags.split(",") if tag.strip())
    return tuple(tag.strip() for tag in clause_tags if str(tag).strip())


@dataclass
class LegalKnowledgeBase:
    """Persisted TF-IDF index over normalized legal guidance notes."""

    vectorizer: TfidfVectorizer
    matrix: object
    records: list[LegalGuidanceRecord]

    def search(self, query: str, top_k: int = 5) -> list[RetrievalHit]:
        """Return the most relevant legal notes for a query."""
        if not query.strip() or not self.records:
            return []

        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.matrix).ravel()

        ranked = similarities.argsort()[::-1][:top_k]
        hits: list[RetrievalHit] = []
        for index in ranked:
            score = float(similarities[index])
            if score <= 0:
                continue
            hits.append(RetrievalHit(record=self.records[index], score=score))
        return hits

    def to_frame(self) -> pd.DataFrame:
        """Return the indexed passages as a dataframe for inspection."""
        return pd.DataFrame(
            [
                {
                    "id": record.id,
                    "title": record.title,
                    "topic": record.topic,
                    "source_name": record.source_name,
                    "source_url": record.source_url,
                    "passage": record.passage,
                    "risk_signal": record.risk_signal,
                }
                for record in self.records
            ]
        )


def build_retrieval_query(
    text: str,
    *,
    predicted_type: str | None = None,
    clause_tags: Sequence[str] | str | None = (),
) -> RetrievalQuery:
    """Create a retrieval query enriched with clause metadata."""
    normalized_tags = _normalize_clause_tags(clause_tags)
    return RetrievalQuery(
        text=text.strip(),
        predicted_type=predicted_type.strip() if predicted_type else None,
        clause_tags=normalized_tags,
    )


def select_top_hits(
    hits: Sequence[RetrievalHit],
    *,
    top_k: int = 5,
    min_score: float = 0.0,
) -> list[RetrievalHit]:
    """Deduplicate and rank hits by score for downstream evidence selection."""
    ranked: dict[str, RetrievalHit] = {}
    for hit in hits:
        if hit.score < min_score:
            continue
        existing = ranked.get(hit.record.id)
        if existing is None or hit.score > existing.score:
            ranked[hit.record.id] = hit

    return sorted(ranked.values(), key=lambda item: item.score, reverse=True)[:top_k]


def retrieve_clause_guidance(
    knowledge_base: LegalKnowledgeBase,
    clause_text: str,
    *,
    predicted_type: str | None = None,
    clause_tags: Sequence[str] | str | None = (),
    top_k: int = 5,
    min_score: float = 0.0,
) -> list[RetrievalHit]:
    """Fetch the most relevant guidance passages for one clause."""
    query = build_retrieval_query(
        clause_text,
        predicted_type=predicted_type,
        clause_tags=clause_tags,
    )
    hits = knowledge_base.search(query.as_text(), top_k=max(top_k * 2, top_k))
    return select_top_hits(hits, top_k=top_k, min_score=min_score)


def retrieve_contract_guidance(
    knowledge_base: LegalKnowledgeBase,
    contract_text: str,
    *,
    clause_predictions: Sequence[Mapping[str, object]] | Sequence[RetrievalQuery] = (),
    top_k: int = 5,
    min_score: float = 0.0,
) -> list[RetrievalHit]:
    """Fetch the most relevant guidance passages for an entire contract."""
    hits: list[RetrievalHit] = []

    if clause_predictions:
        for item in clause_predictions:
            if isinstance(item, RetrievalQuery):
                clause_query = item
            else:
                raw_predicted_type = item.get("predicted_type", "")
                if raw_predicted_type is None:
                    predicted_type = None
                else:
                    predicted_type = str(raw_predicted_type).strip() or None
                clause_query = build_retrieval_query(
                    str(item.get("clause_text", "")),
                    predicted_type=predicted_type,
                    clause_tags=item.get("clause_tags", ()),
                )
            hits.extend(
                knowledge_base.search(
                    clause_query.as_text(),
                    top_k=max(top_k * 2, top_k),
                )
            )
    else:
        hits.extend(knowledge_base.search(contract_text, top_k=max(top_k * 2, top_k)))

    return select_top_hits(hits, top_k=top_k, min_score=min_score)


def retrieve_best_practices(
    knowledge_base: LegalKnowledgeBase,
    topic: str,
    *,
    top_k: int = 3,
    min_score: float = 0.0,
) -> list[RetrievalHit]:
    """Fetch best-practice style guidance for a topic."""
    query = f"best practices {topic.strip()}".strip()
    hits = knowledge_base.search(query, top_k=max(top_k * 2, top_k))
    return select_top_hits(hits, top_k=top_k, min_score=min_score)


def build_knowledge_base(records: list[LegalGuidanceRecord]) -> LegalKnowledgeBase:
    """Build a local TF-IDF index over legal guidance records."""
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1, max_features=5000)
    documents = [record.search_text for record in records]
    matrix = vectorizer.fit_transform(documents)
    return LegalKnowledgeBase(vectorizer=vectorizer, matrix=matrix, records=list(records))


def save_knowledge_base(knowledge_base: LegalKnowledgeBase, path: str | Path = DEFAULT_KB_PATH) -> Path:
    """Persist the knowledge base to disk."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(knowledge_base, destination)
    return destination


def load_knowledge_base(path: str | Path = DEFAULT_KB_PATH) -> LegalKnowledgeBase:
    """Load a previously saved knowledge base."""
    return joblib.load(Path(path))
