"""Structured report assembly for the assistant layer."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from typing import Any

from contract_risk.assistant.explanations import build_clause_explanation
from contract_risk.assistant.guardrails import MIN_EVIDENCE_SCORE, STRICT_GENERATION_TEMPLATE
from contract_risk.assistant.state import AgentState

REPORT_VERSION = "2.0"
LEGAL_DISCLAIMER = (
    "This report is informational only and is not legal advice. "
    "A qualified lawyer should review all contract decisions."
)


def build_clause_references(state: AgentState) -> list[dict[str, Any]]:
    """Create a UI-friendly index of the clauses that were reviewed."""
    references: list[dict[str, Any]] = []
    for finding in state.findings:
        evidence_ids = [item.source_id for item in finding.evidence]
        references.append(
            {
                "clause_id": finding.clause_id,
                "predicted_type": finding.predicted_type,
                "severity": finding.severity,
                "risk_score": finding.risk_score,
                "evidence_ids": evidence_ids,
                "evidence_count": len(evidence_ids),
                "clause_text": finding.clause_text,
            }
        )
    return references


def build_clause_explanations(state: AgentState) -> list[dict[str, Any]]:
    """Create a structured explanation block for each risky clause."""
    explanations: list[dict[str, Any]] = []
    for finding in state.findings:
        explanation = build_clause_explanation(finding, finding.evidence)
        explanations.append(explanation.asdict())
    return explanations


def build_severity_assessment(state: AgentState) -> dict[str, Any]:
    """Summarize severity counts in a deterministic structure."""
    severity_totals = Counter(pred.severity for pred in state.clause_predictions)
    high_count = severity_totals.get("High", 0)
    medium_count = severity_totals.get("Medium", 0)
    low_count = severity_totals.get("Low", 0)

    if high_count:
        overall = "High"
    elif medium_count:
        overall = "Medium"
    else:
        overall = "Low"

    return {
        "high_risk_count": high_count,
        "medium_risk_count": medium_count,
        "low_risk_count": low_count,
        "overall_risk_level": overall,
    }


def build_structured_report(state: AgentState) -> dict[str, Any]:
    """Serialize the assistant state into a stable report payload."""
    assert state.summary is not None

    findings = [asdict(finding) for finding in state.findings]
    mitigation_actions = [finding["mitigation_action"] for finding in findings]
    unique_actions = list(dict.fromkeys(mitigation_actions))

    sources = []
    seen_sources: set[str] = set()
    for finding in state.findings:
        for evidence in finding.evidence:
            if evidence.source_id in seen_sources:
                continue
            seen_sources.add(evidence.source_id)
            sources.append(
                {
                    "source_id": evidence.source_id,
                    "title": evidence.source_title,
                    "url": evidence.source_url,
                }
            )

    return {
        "report_version": REPORT_VERSION,
        "contract_summary": asdict(state.summary),
        "severity_assessment": build_severity_assessment(state),
        "identified_risks": findings,
        "clause_references": build_clause_references(state),
        "clause_explanations": build_clause_explanations(state),
        "mitigation_actions": unique_actions,
        "disclaimer": LEGAL_DISCLAIMER,
        "generation_controls": {
            "min_evidence_score": MIN_EVIDENCE_SCORE,
            "citation_policy": "cite sources when evidence is strong; refuse to speculate when evidence is weak or missing",
            "prompt_template": STRICT_GENERATION_TEMPLATE,
        },
        "sources_consulted": sources,
        "fallback": {
            "used": state.fallback_reason is not None,
            "reason": state.fallback_reason,
            "errors": list(state.errors),
        },
    }
