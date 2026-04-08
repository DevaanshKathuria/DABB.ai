"""Tests for multi-contract comparison and trend analysis."""

from __future__ import annotations

from dataclasses import dataclass

from contract_risk.assistant.comparison import build_risk_trend_summary
from contract_risk.assistant.corpus import load_legal_guidance_corpus
from contract_risk.assistant.retrieval import build_knowledge_base
from contract_risk.ui_support import analyze_contract_text


@dataclass
class _ToyModel:
    def predict(self, batch: list[str]) -> list[str]:
        return ["termination" for _ in batch]


def test_build_risk_trend_summary_finds_repeated_patterns() -> None:
    knowledge_base = build_knowledge_base(load_legal_guidance_corpus())
    analysis_one = analyze_contract_text(
        "Either party may terminate on written notice.",
        _ToyModel(),
        contract_name="Contract One",
        knowledge_base=knowledge_base,
    )
    analysis_two = analyze_contract_text(
        "Termination rights are triggered after 30 days.",
        _ToyModel(),
        contract_name="Contract Two",
        knowledge_base=knowledge_base,
    )

    summary = build_risk_trend_summary([analysis_one, analysis_two])

    assert summary["contract_count"] == 2
    assert summary["severity_totals"]["High"] >= 2
    assert summary["per_contract"][0]["contract_name"] == "Contract One"
    assert summary["repeated_risk_patterns"]
    assert summary["repeated_risk_patterns"][0]["contract_count"] == 2
    assert "Contract One" in summary["repeated_risk_patterns"][0]["contracts"]


def test_build_risk_trend_summary_ignores_missing_reports() -> None:
    knowledge_base = build_knowledge_base(load_legal_guidance_corpus())
    analysis = analyze_contract_text(
        "Termination clause with notice.",
        _ToyModel(),
        contract_name="Working Contract",
        knowledge_base=knowledge_base,
    )
    summary = build_risk_trend_summary([analysis, analyze_contract_text("", _ToyModel(), contract_name="Empty")])

    assert summary["contract_count"] == 1
    assert summary["per_contract"][0]["contract_name"] == "Working Contract"
