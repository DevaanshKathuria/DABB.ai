"""Backend report generation for the legal assistant."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from contract_risk.assistant.corpus import load_legal_guidance_corpus
from contract_risk.assistant.retrieval import (
    DEFAULT_KB_PATH,
    LegalKnowledgeBase,
    RetrievalHit,
    build_knowledge_base,
    load_knowledge_base,
    save_knowledge_base,
)
from contract_risk.assistant.state import (
    AgentState,
    ClausePrediction,
    EvidenceItem,
    RiskFinding,
    WorkflowStage,
)
from contract_risk.assistant.workflow import build_summary, complete_workflow, create_agent_state, mark_fallback, mark_mitigation
from contract_risk.risk.mapping import map_clause_type_to_risk

LEGAL_DISCLAIMER = (
    "This report is informational only and is not legal advice. "
    "A qualified lawyer should review all contract decisions."
)

MITIGATION_GUIDANCE: dict[str, str] = {
    "termination": "Clarify notice periods, cure rights, transition duties, and survival obligations.",
    "liability": "Add a liability cap, narrow carve-outs, and confirm insurance / indemnity wording.",
    "force majeure": "List the triggering events, notice rules, and any mitigation duties.",
    "arbitration": "Define the seat, rules, number of arbitrators, and whether court relief is preserved.",
    "confidentiality": "Define confidential data, exclusions, duration, and permitted disclosures.",
    "payment terms": "State invoice timing, due dates, late fees, taxes, and dispute windows.",
    "governing law": "Align governing law with venue and forum-selection language.",
    "dispute resolution": "Specify escalation steps and the order of mediation, arbitration, or court action.",
}


def _normalize_prediction(item: ClausePrediction | Mapping[str, Any]) -> ClausePrediction:
    """Normalize raw clause prediction payloads into a typed object."""
    if isinstance(item, ClausePrediction):
        return item

    clause_text = str(item.get("clause_text", "")).strip()
    predicted_type = str(item.get("predicted_type", "")).strip() or "unknown"
    risk = map_clause_type_to_risk(predicted_type)
    severity = str(item.get("severity", risk.severity)).strip() or risk.severity
    raw_score = item.get("risk_score", risk.score)
    try:
        risk_score = int(raw_score)
    except (TypeError, ValueError):
        risk_score = risk.score

    return ClausePrediction(
        clause_id=str(item.get("clause_id", "")).strip() or "C000",
        clause_text=clause_text,
        predicted_type=predicted_type,
        severity=severity,
        risk_score=risk_score,
    )


def _load_or_build_knowledge_base(path: str | Path = DEFAULT_KB_PATH) -> LegalKnowledgeBase:
    """Load the persisted KB or build it from the bundled legal corpus."""
    kb_path = Path(path)
    if kb_path.exists():
        return load_knowledge_base(kb_path)

    corpus = load_legal_guidance_corpus()
    knowledge_base = build_knowledge_base(corpus)
    save_knowledge_base(knowledge_base, kb_path)
    return knowledge_base


def _evidence_from_hits(clause_id: str, hits: list[RetrievalHit]) -> tuple[EvidenceItem, ...]:
    """Translate retrieval hits into serializable evidence items."""
    evidence: list[EvidenceItem] = []
    for hit in hits:
        evidence.append(
            EvidenceItem(
                clause_id=clause_id,
                source_id=hit.record.id,
                source_title=hit.record.title,
                source_url=hit.record.source_url,
                snippet=hit.record.passage,
                score=round(hit.score, 4),
            )
        )
    return tuple(evidence)


def _build_mitigation_action(prediction: ClausePrediction) -> str:
    """Return a compact mitigation action for the predicted clause type."""
    key = prediction.predicted_type.lower().strip()
    return MITIGATION_GUIDANCE.get(
        key,
        "Review the clause wording, add explicit guardrails, and confirm the allocation of risk.",
    )


def _build_finding(
    prediction: ClausePrediction,
    evidence: tuple[EvidenceItem, ...],
) -> RiskFinding:
    """Build a structured clause-level risk finding."""
    mitigation = _build_mitigation_action(prediction)
    explanation = (
        f"The clause is classified as {prediction.severity.lower()} risk because it matches "
        f"the project's rule-based mapping for {prediction.predicted_type} clauses."
    )
    if evidence:
        explanation += f" Retrieval support was found in {evidence[0].source_title}."
    else:
        explanation += " Retrieval support was limited, so the fallback rule path was used."

    return RiskFinding(
        clause_id=prediction.clause_id,
        clause_text=prediction.clause_text,
        predicted_type=prediction.predicted_type,
        severity=prediction.severity,
        risk_score=prediction.risk_score,
        explanation=explanation,
        mitigation_action=mitigation,
        evidence=evidence,
    )


def _report_sections(state: AgentState) -> dict[str, Any]:
    """Serialize the assistant state into a report payload."""
    assert state.summary is not None

    severity_totals = Counter(pred.severity for pred in state.clause_predictions)
    findings = [asdict(finding) for finding in state.findings]

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

    mitigation_actions = [finding.mitigation_action for finding in state.findings]
    unique_actions = list(dict.fromkeys(mitigation_actions))

    return {
        "contract_summary": asdict(state.summary),
        "risk_severity_assessment": {
            "high": severity_totals.get("High", 0),
            "medium": severity_totals.get("Medium", 0),
            "low": severity_totals.get("Low", 0),
        },
        "identified_risks": findings,
        "recommended_mitigation_actions": unique_actions,
        "legal_and_ethical_disclaimer": LEGAL_DISCLAIMER,
        "fallback": {
            "used": state.fallback_reason is not None,
            "reason": state.fallback_reason,
            "errors": list(state.errors),
        },
        "sources_consulted": sources,
    }


def generate_legal_assistance_report(
    contract_text: str,
    clause_predictions: Sequence[ClausePrediction | Mapping[str, Any]],
    *,
    knowledge_base: LegalKnowledgeBase | None = None,
    contract_name: str = "Uploaded Contract",
    top_k: int = 3,
) -> dict[str, Any]:
    """Generate a structured draft legal risk report from clause predictions."""
    normalized_predictions = [_normalize_prediction(item) for item in clause_predictions]
    state = create_agent_state(contract_text, normalized_predictions)

    if not contract_text.strip() or not normalized_predictions:
        mark_fallback(state, "Contract text or clause predictions were missing.")
        build_summary(state, contract_name=contract_name)
        complete_workflow(state)
        return _report_sections(state)

    kb = knowledge_base or _load_or_build_knowledge_base()
    if not kb.records:
        mark_fallback(state, "No legal guidance corpus was available for retrieval.")

    build_summary(state, contract_name=contract_name)

    for prediction in normalized_predictions:
        query = f"{prediction.predicted_type} {prediction.clause_text}".strip()
        hits = kb.search(query, top_k=top_k) if kb.records else []
        evidence = _evidence_from_hits(prediction.clause_id, hits)
        if evidence:
            state.evidence.extend(evidence)
        finding = _build_finding(prediction, evidence)
        state.findings.append(finding)

    mark_mitigation(state)
    complete_workflow(state)
    return _report_sections(state)
