"""Tests for the structured legal assistance report generator."""

from contract_risk.assistant.corpus import load_legal_guidance_corpus
from contract_risk.assistant.retrieval import build_knowledge_base
from contract_risk.assistant.service import generate_legal_assistance_report


def test_generate_report_returns_structured_sections() -> None:
    kb = build_knowledge_base(load_legal_guidance_corpus())
    report = generate_legal_assistance_report(
        "Contract text about termination and arbitration.",
        [
            {
                "clause_id": "C001",
                "clause_text": "Either party may terminate with notice.",
                "predicted_type": "termination",
                "severity": "High",
                "risk_score": 90,
            },
            {
                "clause_id": "C002",
                "clause_text": "All disputes go to arbitration.",
                "predicted_type": "arbitration",
                "severity": "Medium",
                "risk_score": 65,
            },
        ],
        knowledge_base=kb,
        contract_name="Demo Agreement",
    )

    assert report["report_version"] == "2.0"
    assert report["contract_summary"]["contract_name"] == "Demo Agreement"
    assert report["severity_assessment"]["high_risk_count"] == 1
    assert len(report["identified_risks"]) == 2
    assert len(report["clause_references"]) == 2
    assert report["mitigation_actions"]
    assert report["disclaimer"]
    assert report["sources_consulted"]


def test_generate_report_clauses_remain_easy_to_render() -> None:
    kb = build_knowledge_base(load_legal_guidance_corpus())
    report = generate_legal_assistance_report(
        "Arbitration and termination notice text.",
        [
            {
                "clause_id": "C010",
                "clause_text": "The contract may terminate on written notice.",
                "predicted_type": "termination",
                "severity": "High",
                "risk_score": 88,
            },
        ],
        knowledge_base=kb,
        contract_name="Render Test",
    )

    clause_reference = report["clause_references"][0]
    assert clause_reference["clause_id"] == "C010"
    assert clause_reference["evidence_count"] >= 1
    assert "clause_text" in clause_reference


def test_generate_report_uses_fallback_for_empty_input() -> None:
    report = generate_legal_assistance_report("", [], contract_name="Empty Contract")
    assert report["fallback"]["used"] is True
    assert report["contract_summary"]["contract_name"] == "Empty Contract"
    assert report["disclaimer"]
