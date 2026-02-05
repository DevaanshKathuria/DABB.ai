"""Streamlit UI for milestone-1 contract text ingestion and segmentation."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from contract_risk.data.ingestion import UnsupportedFileTypeError, extract_text_from_upload
from contract_risk.features.segmentation import segment_clauses

st.set_page_config(page_title="DABB.ai Contract Risk Analyzer", layout="wide")
st.title("DABB.ai - Intelligent Contract Risk Analysis (Milestone 1)")
st.caption("Upload a TXT or PDF contract to extract and segment clauses.")

uploaded_file = st.file_uploader("Upload contract", type=["txt", "pdf"])

if uploaded_file is not None:
    try:
        raw_text = extract_text_from_upload(uploaded_file.name, uploaded_file.getvalue())
    except UnsupportedFileTypeError as exc:
        st.error(str(exc))
        st.stop()

    if not raw_text:
        st.warning("No text could be extracted from the uploaded document.")
        st.stop()

    clauses = segment_clauses(raw_text)
    clause_df = pd.DataFrame(
        {
            "clause_id": [f"C{i+1:03d}" for i in range(len(clauses))],
            "clause_text": clauses,
        }
    )

    with st.expander("Extracted Text", expanded=False):
        st.text_area("Raw extracted text", value=raw_text, height=260)

    st.subheader("Segmented Clauses")
    st.dataframe(clause_df, use_container_width=True)

    st.subheader("Clause Blocks")
    for _, row in clause_df.iterrows():
        st.markdown(f"**{row['clause_id']}**")
        st.write(row["clause_text"])
        st.divider()
else:
    st.info("Upload a `.txt` or `.pdf` contract to begin.")
