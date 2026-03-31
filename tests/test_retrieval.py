"""Tests for the local legal guidance retrieval index."""

from pathlib import Path

from contract_risk.assistant.corpus import load_legal_guidance_corpus
from contract_risk.assistant.retrieval import (
    RetrievalHit,
    build_knowledge_base,
    load_knowledge_base,
    retrieve_best_practices,
    retrieve_clause_guidance,
    retrieve_contract_guidance,
    save_knowledge_base,
    select_top_hits,
)


def test_retrieval_returns_relevant_force_majeure_note() -> None:
    knowledge_base = build_knowledge_base(load_legal_guidance_corpus())
    hits = retrieve_clause_guidance(
        knowledge_base,
        "pandemic and business interruption under force majeure",
        predicted_type="force majeure",
        clause_tags=("force majeure",),
        top_k=3,
    )
    assert hits
    assert hits[0].record.id == "force-majeure"


def test_contract_guidance_ranks_top_contract_topics() -> None:
    knowledge_base = build_knowledge_base(load_legal_guidance_corpus())
    hits = retrieve_contract_guidance(
        knowledge_base,
        "Termination notice and arbitration for disputes.",
        clause_predictions=[
            {"clause_text": "Either party may terminate on notice.", "predicted_type": "termination"},
            {"clause_text": "Disputes must go to arbitration.", "predicted_type": "arbitration"},
        ],
        top_k=2,
    )

    assert {hit.record.id for hit in hits} == {"arbitration", "termination-convenience"}
    assert hits[0].record.id == "termination-convenience"


def test_select_top_hits_deduplicates_by_record_id() -> None:
    records = load_legal_guidance_corpus()
    first = records[0]
    second = records[1]
    hits = [
        RetrievalHit(record=first, score=0.12),
        RetrievalHit(record=first, score=0.55),
        RetrievalHit(record=second, score=0.44),
    ]

    ranked = select_top_hits(hits, top_k=2, min_score=0.1)
    assert [hit.record.id for hit in ranked] == [first.id, second.id]
    assert ranked[0].score == 0.55


def test_best_practices_lookup_prefers_topic_query() -> None:
    knowledge_base = build_knowledge_base(load_legal_guidance_corpus())
    hits = retrieve_best_practices(knowledge_base, "arbitration", top_k=2)
    assert hits
    assert hits[0].record.topic == "dispute resolution"


def test_knowledge_base_round_trip(tmp_path: Path) -> None:
    knowledge_base = build_knowledge_base(load_legal_guidance_corpus())
    destination = save_knowledge_base(knowledge_base, tmp_path / "kb.joblib")
    restored = load_knowledge_base(destination)

    hits = restored.search("arbitration clause dispute resolution")
    assert hits
    assert hits[0].record.topic in {"dispute resolution", "termination"}
