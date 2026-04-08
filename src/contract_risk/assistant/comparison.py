"""Risk comparison helpers for multiple contract uploads."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Sequence

from contract_risk.ui_support import ContractAnalysisResult


def build_risk_trend_summary(analyses: Sequence[ContractAnalysisResult]) -> dict[str, Any]:
    """Aggregate multiple contract reports into repeated risk patterns."""
    per_contract: list[dict[str, Any]] = []
    severity_totals: Counter[str] = Counter()
    pattern_occurrences: dict[str, list[str]] = defaultdict(list)

    for analysis in analyses:
        if not analysis.report:
            continue

        findings = analysis.report.get("identified_risks", [])
        contract_severities: Counter[str] = Counter()
        contract_types: Counter[str] = Counter()

        for finding in findings:
            severity = str(finding.get("severity", "Medium"))
            predicted_type = str(finding.get("predicted_type", "unknown"))
            severity_totals[severity] += 1
            contract_severities[severity] += 1
            contract_types[predicted_type] += 1
            pattern_occurrences[predicted_type].append(analysis.contract_name)

        per_contract.append(
            {
                "contract_name": analysis.contract_name,
                "clause_count": analysis.report.get("contract_summary", {}).get("clause_count", len(findings)),
                "high_risk_count": contract_severities.get("High", 0),
                "medium_risk_count": contract_severities.get("Medium", 0),
                "low_risk_count": contract_severities.get("Low", 0),
                "dominant_risk_type": contract_types.most_common(1)[0][0] if contract_types else "unknown",
            }
        )

    repeated_risk_patterns: list[dict[str, Any]] = []
    for predicted_type, contract_names in pattern_occurrences.items():
        unique_contracts = sorted(set(contract_names))
        if len(unique_contracts) < 2:
            continue
        repeated_risk_patterns.append(
            {
                "predicted_type": predicted_type,
                "occurrences": len(contract_names),
                "contract_count": len(unique_contracts),
                "contracts": ", ".join(unique_contracts),
            }
        )

    repeated_risk_patterns.sort(key=lambda item: (item["contract_count"], item["occurrences"]), reverse=True)

    return {
        "contract_count": len(per_contract),
        "severity_totals": dict(severity_totals),
        "per_contract": per_contract,
        "repeated_risk_patterns": repeated_risk_patterns,
    }
