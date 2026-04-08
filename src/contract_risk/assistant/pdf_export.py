"""PDF export helpers for the structured legal assistance report."""

from __future__ import annotations

from io import BytesIO
from textwrap import wrap
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

PDF_WIDTH = 8.5
PDF_HEIGHT = 11.0
LEFT_MARGIN = 0.06
TOP_MARGIN = 0.96
BOTTOM_MARGIN = 0.06
LINE_HEIGHT = 0.025


def _new_page(pdf: PdfPages, title: str) -> tuple[plt.Figure, Any]:
    """Create a blank PDF page with the given title."""
    fig = plt.figure(figsize=(PDF_WIDTH, PDF_HEIGHT))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    fig.text(LEFT_MARGIN, TOP_MARGIN, title, fontsize=16, fontweight="bold", va="top")
    return fig, ax


def _write_wrapped_lines(fig: plt.Figure, start_y: float, paragraphs: list[str], width: int = 92) -> float:
    """Write wrapped paragraphs onto the current figure."""
    cursor = start_y
    for paragraph in paragraphs:
        lines = wrap(paragraph, width=width) or [""]
        for line in lines:
            if cursor <= BOTTOM_MARGIN:
                return cursor
            fig.text(LEFT_MARGIN, cursor, line, fontsize=9, va="top")
            cursor -= LINE_HEIGHT
        cursor -= LINE_HEIGHT * 0.6
    return cursor


def build_legal_assistance_report_pdf(report: dict[str, Any]) -> bytes:
    """Render the structured report into a small multi-page PDF artifact."""
    buffer = BytesIO()

    summary = report["contract_summary"]
    severity = report["severity_assessment"]
    findings = report.get("identified_risks", [])
    mitigation_actions = report.get("mitigation_actions", [])
    sources = report.get("sources_consulted", [])
    disclaimer = report.get("disclaimer", "")

    with PdfPages(buffer) as pdf:
        fig, _ = _new_page(pdf, "DABB.ai Legal Assistance Report")
        y = 0.90
        summary_lines = [
            f"Contract: {summary['contract_name']}",
            f"Clauses reviewed: {summary['clause_count']}",
            f"Risk profile: {severity['overall_risk_level']} "
            f"(High: {severity['high_risk_count']}, Medium: {severity['medium_risk_count']}, Low: {severity['low_risk_count']})",
            summary["overview"],
        ]
        y = _write_wrapped_lines(fig, y, summary_lines)
        y = _write_wrapped_lines(fig, y, [f"Disclaimer: {disclaimer}"])
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig, _ = _new_page(pdf, "Top Findings")
        y = 0.90
        if findings:
            for finding in findings[:10]:
                finding_lines = [
                    f"{finding['clause_id']} - {finding['predicted_type']} - "
                    f"Severity {finding['severity']} - Risk {finding['risk_score']}",
                    finding["explanation"],
                    f"Mitigation: {finding['mitigation_action']}",
                ]
                evidence = finding.get("evidence", [])
                if evidence:
                    lead = evidence[0]
                    finding_lines.append(
                        f"Evidence: {lead['source_title']} ({lead['score']:.2f}) - {lead['snippet']}"
                    )
                y = _write_wrapped_lines(fig, y, finding_lines)
                if y <= BOTTOM_MARGIN + 0.08:
                    break
                y -= LINE_HEIGHT
        else:
            y = _write_wrapped_lines(fig, y, ["No risky clauses were identified in the report."])
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig, _ = _new_page(pdf, "Mitigation and Sources")
        y = 0.90
        mitigation_lines = ["Mitigation actions:"]
        mitigation_lines.extend(f"- {item}" for item in mitigation_actions or ["No mitigation actions were generated."])
        y = _write_wrapped_lines(fig, y, mitigation_lines)
        source_lines = ["Sources consulted:"]
        source_lines.extend(
            f"- {source['source_id']}: {source['title']}" for source in sources or [{"source_id": "N/A", "title": "No sources consulted"}]
        )
        y = _write_wrapped_lines(fig, y, source_lines)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    buffer.seek(0)
    return buffer.getvalue()
