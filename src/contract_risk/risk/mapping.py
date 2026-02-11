"""Map predicted clause types to severity labels and numeric risk scores."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskProfile:
    """Risk profile for a clause type."""

    severity: str
    score: int


RISK_MAPPING: dict[str, RiskProfile] = {
    "indemnity": RiskProfile("High", 90),
    "liability": RiskProfile("High", 88),
    "termination": RiskProfile("High", 82),
    "dispute resolution": RiskProfile("Medium", 65),
    "force majeure": RiskProfile("Medium", 60),
    "payment terms": RiskProfile("Medium", 58),
    "governing law": RiskProfile("Low", 35),
    "confidentiality": RiskProfile("Low", 30),
}

DEFAULT_RISK = RiskProfile("Medium", 50)


def normalize_label(label: str) -> str:
    """Normalize model labels for stable risk lookup."""
    return " ".join(label.lower().strip().split())


def map_clause_type_to_risk(clause_type: str) -> RiskProfile:
    """Return the risk profile associated with a clause type."""
    normalized = normalize_label(clause_type)
    return RISK_MAPPING.get(normalized, DEFAULT_RISK)


def risk_badge_color(severity: str) -> str:
    """Return a visual color token for severity."""
    severity_norm = severity.lower().strip()
    if severity_norm == "high":
        return "#f94144"
    if severity_norm == "medium":
        return "#f8961e"
    return "#43aa8b"
