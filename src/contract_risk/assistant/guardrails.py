"""Prompt and fallback guardrails for assistant generation."""

from __future__ import annotations

from collections.abc import Sequence

from contract_risk.assistant.state import ClausePrediction, EvidenceItem

MIN_EVIDENCE_SCORE = 0.15

STRICT_GENERATION_TEMPLATE = (
    "Use only the retrieved legal guidance.\n"
    "If evidence is missing or weak, state that the evidence is insufficient and refuse to speculate.\n"
    "If evidence exists, cite the source title and URL.\n"
    "Keep explanations concise, plain-language, and tied to the clause at hand."
)


def evidence_is_strong(
    evidence: Sequence[EvidenceItem],
    *,
    min_score: float = MIN_EVIDENCE_SCORE,
) -> bool:
    """Return True when the evidence is strong enough to cite."""
    return bool(evidence) and max(item.score for item in evidence) >= min_score


def filter_supported_evidence(
    evidence: Sequence[EvidenceItem],
    *,
    min_score: float = MIN_EVIDENCE_SCORE,
) -> tuple[EvidenceItem, ...]:
    """Keep only evidence that clears the support threshold."""
    return tuple(item for item in evidence if item.score >= min_score)


def build_generation_prompt(
    prediction: ClausePrediction,
    evidence: Sequence[EvidenceItem],
) -> str:
    """Build a hardened prompt template for future model-backed generation."""
    citation_requirement = "cite sources" if evidence_is_strong(evidence) else "refuse to speculate"
    return (
        f"{STRICT_GENERATION_TEMPLATE}\n"
        f"Clause reference: {prediction.clause_id}\n"
        f"Clause type: {prediction.predicted_type}\n"
        f"Risk level: {prediction.severity}\n"
        f"Directive: {citation_requirement} and stay grounded in retrieved evidence only."
    )
