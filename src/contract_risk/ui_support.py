"""Shared helpers for the Streamlit contract analysis UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

import pandas as pd

from contract_risk.assistant.service import generate_legal_assistance_report
from contract_risk.features.segmentation import segment_clauses
from contract_risk.models.inference import predict_clauses
from contract_risk.risk.mapping import map_clause_type_to_risk

MAX_INPUT_CHARS = 500_000
MAX_CLAUSES = 1500


@dataclass(frozen=True)
class ContractAnalysisResult:
    """Container for one analyzed contract and any non-fatal warnings."""

    contract_name: str
    raw_text: str
    clauses: tuple[str, ...]
    clause_frame: pd.DataFrame
    report: dict[str, Any] | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)
    report_error: str | None = None


def build_clause_frame(clauses: Sequence[str], predicted_types: Sequence[str]) -> pd.DataFrame:
    """Build the clause table used by the UI and the assistant report."""
    rows: list[dict[str, str | int]] = []
    for i, (clause_text, clause_type) in enumerate(zip(clauses, predicted_types), start=1):
        risk = map_clause_type_to_risk(str(clause_type))
        rows.append(
            {
                "clause_id": f"C{i:03d}",
                "clause_text": clause_text,
                "predicted_type": str(clause_type),
                "severity": risk.severity,
                "risk_score": risk.score,
            }
        )
    return pd.DataFrame(rows)


def analyze_contract_text(
    raw_text: str,
    model: object | None,
    *,
    contract_name: str = "Uploaded Contract",
    knowledge_base: object | None = None,
    generate_report: bool = True,
) -> ContractAnalysisResult:
    """Run the Milestone 1 analysis and optionally build the agentic report."""
    warnings: list[str] = []
    errors: list[str] = []

    normalized_text = raw_text.strip()
    if not normalized_text:
        errors.append("No readable contract text was found.")
        empty_frame = build_clause_frame((), ())
        return ContractAnalysisResult(
            contract_name=contract_name,
            raw_text=normalized_text,
            clauses=(),
            clause_frame=empty_frame,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    if len(normalized_text) > MAX_INPUT_CHARS:
        warnings.append(
            f"Document is large ({len(normalized_text):,} chars). "
            f"Only the first {MAX_INPUT_CHARS:,} chars are analyzed for responsiveness."
        )
        normalized_text = normalized_text[:MAX_INPUT_CHARS]

    clauses = segment_clauses(normalized_text)
    if not clauses:
        errors.append("Could not segment clauses from the document.")
        empty_frame = build_clause_frame((), ())
        return ContractAnalysisResult(
            contract_name=contract_name,
            raw_text=normalized_text,
            clauses=(),
            clause_frame=empty_frame,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    if len(clauses) > MAX_CLAUSES:
        warnings.append(
            f"Detected {len(clauses):,} clauses. "
            f"Only first {MAX_CLAUSES:,} clauses are analyzed to avoid timeout."
        )
        clauses = clauses[:MAX_CLAUSES]

    if model is None:
        errors.append("The classifier model is unavailable.")
        clause_frame = build_clause_frame(clauses, ("unknown",) * len(clauses))
        return ContractAnalysisResult(
            contract_name=contract_name,
            raw_text=normalized_text,
            clauses=tuple(clauses),
            clause_frame=clause_frame,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    try:
        predicted_types = predict_clauses(model, clauses, batch_size=256)
        clause_frame = build_clause_frame(clauses, predicted_types)
    except Exception as exc:  # pragma: no cover - defensive guard for model/runtime failures
        errors.append(f"Clause prediction failed: {exc}")
        clause_frame = build_clause_frame(clauses, ("unknown",) * len(clauses))
        return ContractAnalysisResult(
            contract_name=contract_name,
            raw_text=normalized_text,
            clauses=tuple(clauses),
            clause_frame=clause_frame,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    report = None
    report_error = None
    if generate_report:
        try:
            report = generate_legal_assistance_report(
                normalized_text,
                clause_frame.to_dict(orient="records"),
                knowledge_base=knowledge_base,
                contract_name=contract_name,
            )
        except Exception as exc:  # pragma: no cover - defensive guard for assistant runtime failures
            report_error = f"Could not generate the legal assistance report: {exc}"
            warnings.append(report_error)

    return ContractAnalysisResult(
        contract_name=contract_name,
        raw_text=normalized_text,
        clauses=tuple(clauses),
        clause_frame=clause_frame,
        report=report,
        warnings=tuple(warnings),
        errors=tuple(errors),
        report_error=report_error,
    )
