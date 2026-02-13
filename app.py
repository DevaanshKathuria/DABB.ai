"""Streamlit UI for Milestone-1 contract risk analysis."""

from __future__ import annotations

import sys
import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from contract_risk.data.ingestion import UnsupportedFileTypeError, extract_text_from_upload
from contract_risk.features.segmentation import segment_clauses
from contract_risk.models.inference import load_or_train_model
from contract_risk.risk.mapping import map_clause_type_to_risk, risk_badge_color

st.set_page_config(page_title="DABB.ai Contract Risk Analyzer", layout="wide")
st.title("DABB.ai - Intelligent Contract Risk Analysis")
st.caption("Milestone 1: Classical NLP + ML (TF-IDF + Logistic Regression)")

uploaded_file = st.file_uploader("Upload contract", type=["txt", "pdf"])

if uploaded_file is not None:
    try:
        raw_text = extract_text_from_upload(uploaded_file.name, uploaded_file.getvalue())
    except UnsupportedFileTypeError as exc:
        st.error(str(exc))
        st.stop()

    if not raw_text.strip():
        st.warning("No text could be extracted from the uploaded document.")
        st.stop()

    clauses = segment_clauses(raw_text)
    if not clauses:
        st.warning("Could not segment clauses from the document.")
        st.stop()

    model = load_or_train_model()
    predicted_types = model.predict(clauses)

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

    results_df = pd.DataFrame(rows)

    with st.expander("Extracted Text", expanded=False):
        st.text_area("Raw extracted text", value=raw_text, height=250)

    st.subheader("Filter Results")
    severity_options = sorted(results_df["severity"].unique().tolist())
    type_options = sorted(results_df["predicted_type"].unique().tolist())

    col1, col2 = st.columns(2)
    with col1:
        selected_severity = st.multiselect(
            "Severity",
            options=severity_options,
            default=severity_options,
        )
    with col2:
        selected_types = st.multiselect(
            "Clause Type",
            options=type_options,
            default=type_options,
        )

    filtered_df = results_df[
        results_df["severity"].isin(selected_severity)
        & results_df["predicted_type"].isin(selected_types)
    ].copy()

    st.subheader("Clause Risk Table")

    def _style_row(row: pd.Series) -> list[str]:
        color = risk_badge_color(str(row["severity"]))
        style = f"background-color: {color}22"
        return [style if col in {"severity", "risk_score"} else "" for col in row.index]

    styled = filtered_df.style.apply(_style_row, axis=1)
    st.markdown(styled.to_html(index=False), unsafe_allow_html=True)

    st.subheader("Export Results")
    export_col1, export_col2 = st.columns(2)
    with export_col1:
        csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV",
            data=csv_bytes,
            file_name="contract_risk_results.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with export_col2:
        json_bytes = json.dumps(filtered_df.to_dict(orient="records"), indent=2).encode("utf-8")
        st.download_button(
            "Download JSON",
            data=json_bytes,
            file_name="contract_risk_results.json",
            mime="application/json",
            use_container_width=True,
        )

    st.subheader("Highlighted Clauses")
    risky_df = filtered_df[filtered_df["severity"].isin(["High", "Medium"])].copy()
    if risky_df.empty:
        st.success("No medium/high risk clauses in the selected filters.")
    else:
        for _, row in risky_df.iterrows():
            color = risk_badge_color(str(row["severity"]))
            st.markdown(
                f"""
                <div style='border-left: 8px solid {color}; padding: 0.8rem; margin-bottom: 0.8rem; background: #fffaf4;'>
                    <strong>{row['clause_id']}</strong> | <strong>{row['predicted_type']}</strong>
                    | Severity: <strong>{row['severity']}</strong>
                    | Risk Score: <strong>{row['risk_score']}</strong><br/>
                    <span>{row['clause_text']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.info("Upload a `.txt` or `.pdf` contract to begin.")
