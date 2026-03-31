"""Backend report generation for the legal assistant."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from contract_risk.assistant.corpus import load_legal_guidance_corpus
from contract_risk.assistant.explanations import build_clause_explanation
from contract_risk.assistant.reporting import build_structured_report
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
    explanation = build_clause_explanation(prediction, evidence).why_risky

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
        return build_structured_report(state)

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
    return build_structured_report(state)
