"""Clause-level explanation helpers grounded in retrieved evidence."""

from __future__ import annotations

from dataclasses import dataclass, asdict

from contract_risk.assistant.state import ClausePrediction, EvidenceItem


@dataclass(frozen=True)
class ClauseExplanation:
    """Structured explanation for one risky clause."""

    clause_id: str
    clause_reference: str
    why_risky: str
    supporting_reasoning: str
    source_titles: tuple[str, ...]
    evidence_ids: tuple[str, ...]

    def asdict(self) -> dict[str, object]:
        """Serialize the explanation into a stable dictionary."""
        return asdict(self)


def build_clause_explanation(
    prediction: ClausePrediction,
    evidence: tuple[EvidenceItem, ...],
) -> ClauseExplanation:
    """Build a grounded explanation for a risky clause."""
    clause_reference = f"{prediction.clause_id} ({prediction.predicted_type})"

    if evidence:
        lead_evidence = evidence[0]
        source_titles = tuple(item.source_title for item in evidence)
        evidence_ids = tuple(item.source_id for item in evidence)
        why_risky = (
            f"{prediction.clause_id} is {prediction.severity.lower()} risk because the retrieved guidance "
            f"from {lead_evidence.source_title} says: {lead_evidence.snippet}"
        )
        supporting_reasoning = (
            f"Clause {prediction.clause_id} matches the {prediction.predicted_type} risk pattern and the "
            f"retrieved guidance highlights the same issue in {lead_evidence.source_title}."
        )
    else:
        source_titles = ()
        evidence_ids = ()
        why_risky = (
            f"{prediction.clause_id} is {prediction.severity.lower()} risk because the clause maps to a "
            f"{prediction.predicted_type} pattern, but retrieval did not return strong supporting guidance."
        )
        supporting_reasoning = (
            "The assistant used a conservative fallback explanation because evidence was too weak to cite."
        )

    return ClauseExplanation(
        clause_id=prediction.clause_id,
        clause_reference=clause_reference,
        why_risky=why_risky,
        supporting_reasoning=supporting_reasoning,
        source_titles=source_titles,
        evidence_ids=evidence_ids,
    )
