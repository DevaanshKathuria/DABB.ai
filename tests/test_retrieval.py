"""Tests for the local legal guidance retrieval index."""

from pathlib import Path

from contract_risk.assistant.corpus import load_legal_guidance_corpus
from contract_risk.assistant.retrieval import build_knowledge_base, load_knowledge_base, save_knowledge_base


def test_retrieval_returns_relevant_force_majeure_note() -> None:
    knowledge_base = build_knowledge_base(load_legal_guidance_corpus())
    hits = knowledge_base.search("pandemic and business interruption under force majeure")
    assert hits
    assert hits[0].record.id == "force-majeure"


def test_knowledge_base_round_trip(tmp_path: Path) -> None:
    knowledge_base = build_knowledge_base(load_legal_guidance_corpus())
    destination = save_knowledge_base(knowledge_base, tmp_path / "kb.joblib")
    restored = load_knowledge_base(destination)

    hits = restored.search("arbitration clause dispute resolution")
    assert hits
    assert hits[0].record.topic in {"dispute resolution", "termination"}
