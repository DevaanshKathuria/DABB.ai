"""Tests for clause-level explanation generation."""

from contract_risk.assistant.corpus import load_legal_guidance_corpus
from contract_risk.assistant.explanations import build_clause_explanation
from contract_risk.assistant.retrieval import build_knowledge_base, retrieve_clause_guidance
from contract_risk.assistant.state import ClausePrediction, EvidenceItem


def test_clause_explanation_uses_retrieved_evidence_text() -> None:
    knowledge_base = build_knowledge_base(load_legal_guidance_corpus())
    hits = retrieve_clause_guidance(
        knowledge_base,
        "The clause allows termination on short notice.",
        predicted_type="termination",
        clause_tags=("termination", "notice"),
        top_k=2,
    )
    evidence = tuple(
        EvidenceItem(
            clause_id="C007",
            source_id=hit.record.id,
            source_title=hit.record.title,
            source_url=hit.record.source_url,
            snippet=hit.record.passage,
            score=hit.score,
        )
        for hit in hits
    )

    explanation = build_clause_explanation(
        ClausePrediction("C007", "The clause allows termination on short notice.", "termination", "High", 91),
        evidence,
    )

    assert explanation.clause_reference == "C007 (termination)"
    assert evidence[0].source_title in explanation.why_risky
    assert explanation.evidence_ids[0] == evidence[0].source_id
    assert explanation.source_titles[0] == evidence[0].source_title
    assert "retrieved guidance" in explanation.why_risky.lower()


def test_clause_explanation_falls_back_without_evidence() -> None:
    explanation = build_clause_explanation(
        ClausePrediction("C099", "Bare clause text.", "liability", "Medium", 62),
        (),
    )

    assert "fallback" in explanation.supporting_reasoning.lower()
    assert explanation.evidence_ids == ()
