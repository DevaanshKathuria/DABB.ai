"""Workflow skeleton for the agentic legal assistant."""

from __future__ import annotations

from collections import Counter

from contract_risk.assistant.state import (
    AgentState,
    ClausePrediction,
    ContractSummary,
    EvidenceItem,
    RiskFinding,
    WorkflowStage,
)


def create_agent_state(contract_text: str, clause_predictions: list[ClausePrediction]) -> AgentState:
    """Create the initial workflow state."""
    return AgentState(
        stage=WorkflowStage.INGEST,
        contract_text=contract_text,
        clause_predictions=list(clause_predictions),
    )


def advance_stage(state: AgentState, stage: WorkflowStage) -> AgentState:
    """Move the workflow to the next stage."""
    state.stage = stage
    return state


def add_evidence(state: AgentState, evidence: list[EvidenceItem]) -> AgentState:
    """Attach retrieval evidence to the state."""
    state.evidence.extend(evidence)
    state.stage = WorkflowStage.RETRIEVE
    return state


def add_finding(state: AgentState, finding: RiskFinding) -> AgentState:
    """Attach a clause-level finding to the state."""
    state.findings.append(finding)
    state.stage = WorkflowStage.ASSESS_RISK
    return state


def build_summary(state: AgentState, contract_name: str = "Uploaded Contract") -> ContractSummary:
    """Derive a short contract summary from the current findings."""
    severity_counts = Counter(prediction.severity.lower() for prediction in state.clause_predictions)
    summary = ContractSummary(
        contract_name=contract_name,
        clause_count=len(state.clause_predictions),
        high_risk_count=severity_counts.get("high", 0),
        medium_risk_count=severity_counts.get("medium", 0),
        low_risk_count=severity_counts.get("low", 0),
        overview=(
            f"Contract review covered {len(state.clause_predictions)} clauses "
            f"and highlighted {severity_counts.get('high', 0)} high-risk, "
            f"{severity_counts.get('medium', 0)} medium-risk, and "
            f"{severity_counts.get('low', 0)} low-risk clauses."
        ),
    )
    state.summary = summary
    state.stage = WorkflowStage.SUMMARIZE
    return summary


def mark_mitigation(state: AgentState) -> AgentState:
    """Move the workflow into mitigation drafting."""
    state.stage = WorkflowStage.MITIGATE
    return state


def mark_fallback(state: AgentState, reason: str) -> AgentState:
    """Capture fallback handling when retrieval or generation is incomplete."""
    state.fallback_reason = reason
    state.errors.append(reason)
    state.stage = WorkflowStage.FALLBACK
    return state


def complete_workflow(state: AgentState) -> AgentState:
    """Mark the workflow complete."""
    state.stage = WorkflowStage.COMPLETE
    return state
