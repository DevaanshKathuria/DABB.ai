"""Tests for assistant guardrails and fallback behavior."""

from contract_risk.assistant.corpus import LegalGuidanceRecord, load_legal_guidance_corpus
from contract_risk.assistant.guardrails import build_generation_prompt
from contract_risk.assistant.retrieval import build_knowledge_base
from contract_risk.assistant.service import generate_legal_assistance_report
from contract_risk.assistant.state import ClausePrediction, EvidenceItem


def test_generation_prompt_requires_citation_or_refusal() -> None:
    prediction = ClausePrediction("C001", "Termination on notice.", "termination", "High", 90)
    prompt = build_generation_prompt(
        prediction,
        (
            EvidenceItem(
                clause_id="C001",
                source_id="termination-convenience",
                source_title="Termination for convenience",
                source_url="https://www.law.cornell.edu/cfr/text/48/52.249-5",
                snippet="Termination clauses should specify who can terminate.",
                score=0.91,
            ),
        ),
    )

    assert "cite sources" in prompt.lower()
    assert "refuse to speculate" in prompt.lower()
    assert "Clause reference: C001" in prompt


def test_report_refuses_to_cite_weak_evidence() -> None:
    kb = build_knowledge_base(load_legal_guidance_corpus())
    report = generate_legal_assistance_report(
        "Termination on notice and arbitration are mentioned.",
        [
            {
                "clause_id": "C010",
                "clause_text": "Either party may terminate on notice.",
                "predicted_type": "termination",
                "severity": "High",
                "risk_score": 88,
            }
        ],
        knowledge_base=kb,
        contract_name="Weak Evidence",
        min_evidence_score=0.99,
    )

    assert report["fallback"]["used"] is True
    assert "support threshold" in report["fallback"]["reason"].lower()
    assert report["clause_explanations"][0]["citations"] == ()


def test_report_handles_missing_evidence_without_speculation() -> None:
    kb = build_knowledge_base(
        [
            LegalGuidanceRecord(
                id="office-policy",
                title="Office policy",
                source_name="Internal Handbook",
                source_url="https://example.com/office-policy",
                jurisdiction="US",
                topic="operations",
                clause_tags=("operations",),
                passage="Parking permits and break room etiquette are covered here.",
                risk_signal="This is unrelated to contract risk guidance.",
            )
        ]
    )
    report = generate_legal_assistance_report(
        "Confidentiality and arbitration obligations.",
        [
            {
                "clause_id": "C020",
                "clause_text": "Disputes must be resolved by arbitration.",
                "predicted_type": "arbitration",
                "severity": "Medium",
                "risk_score": 68,
            }
        ],
        knowledge_base=kb,
        contract_name="Missing Evidence",
    )

    assert report["fallback"]["used"] is True
    assert "no retrieval evidence" in report["fallback"]["reason"].lower()
    assert report["clause_explanations"][0]["citations"] == ()
