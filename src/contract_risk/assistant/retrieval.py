"""Free, local retrieval index for legal guidance passages."""

from __future__ import annotations

from dataclasses import dataclass
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
