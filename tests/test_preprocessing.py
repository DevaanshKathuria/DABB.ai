"""Tests for retrieval-oriented preprocessing."""

from contract_risk.assistant.preprocessing import build_retrieval_chunks, infer_clause_tags


def test_infer_clause_tags_detects_common_risks() -> None:
    tags = infer_clause_tags("The parties agree to arbitration and termination rights.")
    assert "arbitration" in tags
    assert "termination" in tags


def test_build_retrieval_chunks_preserves_clause_identity() -> None:
    text = (
        "1 Confidentiality The recipient shall not disclose confidential information.\n"
        "2 Termination Either party may terminate with 30 days' notice."
    )
    chunks = build_retrieval_chunks(text, source_id="sample-contract", max_clause_chars=120)
    assert len(chunks) == 2
    assert chunks[0].chunk_id.startswith("sample-contract-c001")
    assert "confidentiality" in chunks[0].tags


def test_build_retrieval_chunks_splits_long_passages_cleanly() -> None:
    text = (
        "1 Payment The customer shall pay all fees within fifteen days. "
        "The vendor may invoice monthly. "
        "Late fee applies after the due date."
    )
    chunks = build_retrieval_chunks(text, source_id="billing", max_clause_chars=70)
    assert len(chunks) >= 2
    assert all(chunk.text for chunk in chunks)
