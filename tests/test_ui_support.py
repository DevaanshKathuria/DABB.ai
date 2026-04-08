"""Tests for shared Streamlit UI helpers."""

from __future__ import annotations

from dataclasses import dataclass

from contract_risk.assistant.corpus import load_legal_guidance_corpus
from contract_risk.assistant.retrieval import build_knowledge_base
from contract_risk.ui_support import (
    analyze_contract_text,
    build_clause_detail_index,
    resolve_selected_clause_id,
)


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


def test_clause_drilldown_index_merges_report_sections() -> None:
    knowledge_base = build_knowledge_base(load_legal_guidance_corpus())
    result = analyze_contract_text(
        "Either party may terminate on written notice.",
        _ToyModel(labels=("termination",)),
        contract_name="Drilldown Contract",
        knowledge_base=knowledge_base,
    )

    assert result.report is not None
    detail_index = build_clause_detail_index(result.report)
    clause_detail = detail_index["C001"]
    assert clause_detail["clause_id"] == "C001"
    assert clause_detail["mitigation_action"]
    assert clause_detail["clause_text"]
    assert clause_detail["evidence"] == () or clause_detail["evidence"]


def test_resolve_selected_clause_id_defaults_to_first_available_option() -> None:
    assert resolve_selected_clause_id(["C010", "C011"], "C999") == "C010"
    assert resolve_selected_clause_id(["C010", "C011"], "C011") == "C011"
    assert resolve_selected_clause_id([]) is None
