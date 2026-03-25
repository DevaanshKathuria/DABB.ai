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

    assert report["contract_summary"]["contract_name"] == "Demo Agreement"
    assert len(report["identified_risks"]) == 2
    assert report["recommended_mitigation_actions"]
    assert report["legal_and_ethical_disclaimer"]


def test_generate_report_uses_fallback_for_empty_input() -> None:
    report = generate_legal_assistance_report("", [], contract_name="Empty Contract")
    assert report["fallback"]["used"] is True
    assert report["contract_summary"]["contract_name"] == "Empty Contract"
