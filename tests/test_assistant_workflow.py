"""Tests for the assistant workflow skeleton."""

from contract_risk.assistant.state import ClausePrediction, WorkflowStage
from contract_risk.assistant.workflow import build_summary, create_agent_state, mark_fallback


def test_create_agent_state_initializes_ingest_stage() -> None:
    state = create_agent_state(
        "Contract text",
        [ClausePrediction("C001", "Clause text", "termination", "High", 90)],
    )
    assert state.stage == WorkflowStage.INGEST
    assert state.clause_predictions[0].predicted_type == "termination"


def test_build_summary_counts_risk_levels() -> None:
    state = create_agent_state(
        "Contract text",
        [
            ClausePrediction("C001", "Clause text", "termination", "High", 90),
            ClausePrediction("C002", "Clause text", "payment", "Medium", 60),
        ],
    )
    summary = build_summary(state)
    assert summary.high_risk_count == 1
    assert summary.medium_risk_count == 1
    assert state.stage == WorkflowStage.SUMMARIZE


def test_mark_fallback_records_reason() -> None:
    state = create_agent_state("Contract text", [])
    mark_fallback(state, "retrieval unavailable")
    assert state.stage == WorkflowStage.FALLBACK
    assert state.fallback_reason == "retrieval unavailable"
