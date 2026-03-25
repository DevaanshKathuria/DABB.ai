"""Typed state objects for the legal assistant workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class WorkflowStage(str, Enum):
    """Workflow phases used by the legal assistant."""

    INGEST = "ingest"
    PREPROCESS = "preprocess"
    RETRIEVE = "retrieve"
    SUMMARIZE = "summarize"
    ASSESS_RISK = "assess_risk"
    MITIGATE = "mitigate"
    FALLBACK = "fallback"
    COMPLETE = "complete"


@dataclass(frozen=True)
class ClausePrediction:
    """Normalized clause prediction used by the assistant."""

    clause_id: str
    clause_text: str
    predicted_type: str
    severity: str
    risk_score: int


@dataclass(frozen=True)
class EvidenceItem:
    """Evidence item retrieved for a clause."""

    clause_id: str
    source_id: str
    source_title: str
    source_url: str
    snippet: str
    score: float


@dataclass(frozen=True)
class RiskFinding:
    """Structured clause-level risk finding."""

    clause_id: str
    clause_text: str
    predicted_type: str
    severity: str
    risk_score: int
    explanation: str
    mitigation_action: str
    evidence: tuple[EvidenceItem, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ContractSummary:
    """High-level summary for a contract risk report."""

    contract_name: str
    clause_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    overview: str


@dataclass
class AgentState:
    """Mutable workflow state for the assistant pipeline."""

    stage: WorkflowStage
    contract_text: str
    clause_predictions: list[ClausePrediction]
    evidence: list[EvidenceItem] = field(default_factory=list)
    findings: list[RiskFinding] = field(default_factory=list)
    summary: ContractSummary | None = None
    fallback_reason: str | None = None
    errors: list[str] = field(default_factory=list)
