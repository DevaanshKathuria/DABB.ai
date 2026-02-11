"""Tests for risk mapping rules."""

from contract_risk.risk.mapping import map_clause_type_to_risk, risk_badge_color


def test_known_clause_has_expected_risk() -> None:
    profile = map_clause_type_to_risk("Liability")
    assert profile.severity == "High"
    assert profile.score >= 80


def test_unknown_clause_uses_default_profile() -> None:
    profile = map_clause_type_to_risk("Unknown Clause")
    assert profile.severity == "Medium"
    assert profile.score == 50


def test_badge_color_mapping() -> None:
    assert risk_badge_color("High") == "#f94144"
    assert risk_badge_color("Medium") == "#f8961e"
    assert risk_badge_color("Low") == "#43aa8b"
