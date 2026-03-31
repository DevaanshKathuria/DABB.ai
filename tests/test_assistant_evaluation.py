"""Evaluation-style regression tests for the assistant layer."""

from __future__ import annotations

import json

from contract_risk.assistant.corpus import LegalGuidanceRecord, load_legal_guidance_corpus
from contract_risk.assistant.retrieval import build_knowledge_base
from contract_risk.assistant.service import generate_legal_assistance_report


EXPECTED_REPORT_KEYS = {
    "report_version",
    "contract_summary",
    "severity_assessment",
    "identified_risks",
    "clause_references",
    "clause_explanations",
    "mitigation_actions",
    "disclaimer",
    "generation_controls",
    "sources_consulted",
    "fallback",
}

EXPECTED_FINDING_KEYS = {
    "clause_id",
    "clause_text",
    "predicted_type",
    "severity",
    "risk_score",
    "explanation",
    "mitigation_action",
    "evidence",
}

EXPECTED_EXPLANATION_KEYS = {
    "clause_id",
    "clause_reference",
    "why_risky",
    "supporting_reasoning",
    "source_titles",
    "evidence_ids",
    "citations",
}


def _build_demo_report():
    kb = build_knowledge_base(load_legal_guidance_corpus())
    return generate_legal_assistance_report(
        "Termination and arbitration are both present in the draft.",
        [
            {
                "clause_id": "C100",
                "clause_text": "Either party may terminate on notice.",
                "predicted_type": "termination",
                "severity": "High",
                "risk_score": 90,
            },
            {
                "clause_id": "C200",
                "clause_text": "Disputes must go to arbitration.",
                "predicted_type": "arbitration",
                "severity": "Medium",
                "risk_score": 67,
            },
        ],
        knowledge_base=kb,
        contract_name="Evaluation Agreement",
    )


def test_assistant_report_schema_is_stable() -> None:
    report = _build_demo_report()

    assert EXPECTED_REPORT_KEYS <= set(report)
    assert EXPECTED_FINDING_KEYS <= set(report["identified_risks"][0])
    assert EXPECTED_EXPLANATION_KEYS <= set(report["clause_explanations"][0])
    assert report["contract_summary"]["contract_name"] == "Evaluation Agreement"
    assert report["severity_assessment"]["overall_risk_level"] in {"High", "Medium", "Low"}


def test_assistant_retrieval_fallback_regression() -> None:
    kb = build_knowledge_base(
        [
            LegalGuidanceRecord(
                id="unrelated",
                title="Internal policy",
                source_name="Operations",
                source_url="https://example.com/internal-policy",
                jurisdiction="US",
                topic="operations",
                clause_tags=("operations",),
                passage="Office desk arrangements and parking passes are listed here.",
                risk_signal="Unrelated to legal review.",
            )
        ]
    )
    report = generate_legal_assistance_report(
        "Confidentiality and arbitration obligations.",
        [
            {
                "clause_id": "C300",
                "clause_text": "Disputes must be resolved by arbitration.",
                "predicted_type": "arbitration",
                "severity": "Medium",
                "risk_score": 66,
            }
        ],
        knowledge_base=kb,
        contract_name="Fallback Agreement",
    )

    assert report["fallback"]["used"] is True
    assert "no retrieval evidence" in report["fallback"]["reason"].lower()
    assert report["clause_explanations"][0]["citations"] == ()


def test_assistant_report_format_remains_json_serializable() -> None:
    report = _build_demo_report()
    payload = json.dumps(report, sort_keys=True)

    assert '"report_version": "2.0"' in payload
    assert '"clause_references"' in payload
    assert '"generation_controls"' in payload
