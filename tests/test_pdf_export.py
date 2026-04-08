"""Tests for PDF export of the legal assistance report."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from contract_risk.assistant.corpus import load_legal_guidance_corpus
from contract_risk.assistant.pdf_export import build_legal_assistance_report_pdf
from contract_risk.assistant.retrieval import build_knowledge_base
from contract_risk.assistant.service import generate_legal_assistance_report


def test_pdf_export_generates_parseable_pdf_bytes() -> None:
    kb = build_knowledge_base(load_legal_guidance_corpus())
    report = generate_legal_assistance_report(
        "Contract text about termination and arbitration.",
        [
            {
                "clause_id": "C001",
                "clause_text": "Either party may terminate with notice.",
                "predicted_type": "termination",
                "severity": "High",
                "risk_score": 90,
            },
        ],
        knowledge_base=kb,
        contract_name="PDF Demo",
    )

    pdf_bytes = build_legal_assistance_report_pdf(report)

    assert pdf_bytes[:4] == b"%PDF"
    reader = PdfReader(BytesIO(pdf_bytes))
    assert len(reader.pages) >= 2
    extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "PDF Demo" in extracted_text
    assert "Disclaimer" in extracted_text
    assert "termination" in extracted_text.lower()
