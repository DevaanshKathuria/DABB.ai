"""Tests for shared Streamlit UI helpers."""

from __future__ import annotations

from dataclasses import dataclass

from contract_risk.assistant.corpus import load_legal_guidance_corpus
from contract_risk.assistant.retrieval import build_knowledge_base
from contract_risk.ui_support import analyze_contract_text


@dataclass
class _ToyModel:
    labels: tuple[str, ...] = ("termination", "arbitration")

    def predict(self, batch: list[str]) -> list[str]:
        return [self.labels[i % len(self.labels)] for i, _ in enumerate(batch)]


def test_analyze_contract_text_builds_clause_table_and_report() -> None:
    knowledge_base = build_knowledge_base(load_legal_guidance_corpus())
    result = analyze_contract_text(
        "Either party may terminate on written notice. Disputes go to arbitration.",
        _ToyModel(),
        contract_name="Demo Contract",
        knowledge_base=knowledge_base,
    )

    assert result.contract_name == "Demo Contract"
    assert len(result.clauses) >= 1
    assert not result.clause_frame.empty
    assert list(result.clause_frame.columns) == [
        "clause_id",
        "clause_text",
        "predicted_type",
        "severity",
        "risk_score",
    ]
    assert result.report is not None
    assert result.report["contract_summary"]["contract_name"] == "Demo Contract"
    assert result.report["identified_risks"]


def test_analyze_contract_text_reports_missing_text_without_crashing() -> None:
    result = analyze_contract_text("", _ToyModel(), contract_name="Empty Contract")

    assert result.report is None
    assert result.errors == ("No readable contract text was found.",)
    assert result.clause_frame.empty
