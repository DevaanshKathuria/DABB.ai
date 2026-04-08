"""Streamlit UI for Milestone-1 contract risk analysis."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from contract_risk.assistant.corpus import load_legal_guidance_corpus
from contract_risk.assistant.retrieval import build_knowledge_base
from contract_risk.data.ingestion import (
    DocumentReadError,
    UnsupportedFileTypeError,
    extract_text_from_upload,
)
from contract_risk.models.explainability import ExplainabilityError, top_features_by_class
from contract_risk.models.inference import load_or_train_model
from contract_risk.risk.mapping import risk_badge_color
from contract_risk.ui_support import (
    analyze_contract_text,
    build_clause_detail_index,
    format_clause_label,
    resolve_selected_clause_id,
)

st.set_page_config(page_title="DABB.ai Contract Risk Analyzer", layout="wide")
st.title("DABB.ai - Intelligent Contract Risk Analysis")
st.caption("Milestone 1: Classical NLP + ML (TF-IDF + Logistic Regression)")
st.warning("Informational only, not legal advice.")

MAX_CLAUSES = 1500


@st.cache_resource(show_spinner=False)
def get_cached_model() -> object:
    """Load the trained model once per session."""
    return load_or_train_model()


@st.cache_resource(show_spinner=False)
def get_cached_knowledge_base() -> object:
    """Load the legal guidance corpus once per session."""
    return build_knowledge_base(load_legal_guidance_corpus())


def _render_report(report: dict[str, object] | None, report_error: str | None = None) -> None:
    """Render the structured legal assistance report in the UI."""
    st.subheader("Generate Legal Assistance Report")
    if report_error:
        st.warning(report_error)
    if report is None:
        st.info("Click the button above to generate a structured assistant-backed report.")
        return

    summary = report["contract_summary"]
    severity = report["severity_assessment"]
    fallback = report["fallback"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Contract", summary["contract_name"])
    with col2:
        st.metric("Overall Risk", severity["overall_risk_level"])
    with col3:
        st.metric("Fallback Used", "Yes" if fallback["used"] else "No")

    st.write(summary["overview"])
    if fallback["used"] and fallback["reason"]:
        st.info(fallback["reason"])

    risk_cols = st.columns(3)
    with risk_cols[0]:
        st.metric("High Risk Clauses", severity["high_risk_count"])
    with risk_cols[1]:
        st.metric("Medium Risk Clauses", severity["medium_risk_count"])
    with risk_cols[2]:
        st.metric("Low Risk Clauses", severity["low_risk_count"])

    with st.expander("Assistant Findings", expanded=False):
        for finding in report["identified_risks"]:
            st.markdown(
                f"**{finding['clause_id']}** | **{finding['predicted_type']}** | "
                f"Severity: **{finding['severity']}** | Risk Score: **{finding['risk_score']}**"
            )
            st.write(finding["explanation"])
            st.caption(f"Mitigation: {finding['mitigation_action']}")
            if finding["evidence"]:
                for evidence in finding["evidence"]:
                    st.markdown(
                        f"- **{evidence['source_title']}** "
                        f"({evidence['score']:.2f}): {evidence['snippet']}"
                    )
            else:
                st.info("No strong evidence was cited for this clause.")

    with st.expander("Sources Consulted", expanded=False):
        if report["sources_consulted"]:
            st.dataframe(pd.DataFrame(report["sources_consulted"]), use_container_width=True)
        else:
            st.info("No external sources were consulted.")


def render_app() -> None:
    """Render the full Streamlit application."""
    uploaded_file = st.file_uploader("Upload contract", type=["txt", "pdf"])
    use_demo_mode = st.checkbox("Use bundled demo contract", value=uploaded_file is None)

    if uploaded_file is None and not use_demo_mode:
        st.info("Upload a `.txt` or `.pdf` contract, or enable demo mode to begin.")
        return

    try:
        if uploaded_file is not None:
            raw_text = extract_text_from_upload(uploaded_file.name, uploaded_file.getvalue())
            contract_name = uploaded_file.name
        else:
            raw_text = (ROOT / "data" / "demo" / "demo_contract.txt").read_text(encoding="utf-8")
            contract_name = "Bundled Demo Contract"
    except UnsupportedFileTypeError as exc:
        st.error(str(exc))
        return
    except DocumentReadError as exc:
        st.error(str(exc))
        return
    except FileNotFoundError:
        st.error("Demo contract file is missing.")
        return
    except Exception:
        st.error("Unexpected error while parsing the document.")
        return

    model = get_cached_model()
    knowledge_base = get_cached_knowledge_base()
    analysis = analyze_contract_text(
        raw_text,
        model,
        contract_name=contract_name,
        knowledge_base=knowledge_base,
    )

    for warning in analysis.warnings:
        st.warning(warning)
    for error in analysis.errors:
        st.error(error)

    if analysis.clause_frame.empty:
        st.warning("No clause analysis is available for this document.")
        return

    results_df = analysis.clause_frame.copy()

    with st.expander("Extracted Text", expanded=False):
        st.text_area("Raw extracted text", value=analysis.raw_text, height=250)

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

    st.subheader("Generate Legal Assistance Report")
    if st.button("Generate Legal Assistance Report", use_container_width=True):
        st.session_state["assistant_report"] = analysis.report
        st.session_state["assistant_report_error"] = analysis.report_error
        st.session_state["assistant_report_warnings"] = analysis.warnings

    report_to_render = st.session_state.get("assistant_report")
    if report_to_render is None:
        if st.session_state.get("assistant_report_error"):
            st.warning(st.session_state["assistant_report_error"])
        st.info("Use the button above to generate the assistant-backed report for this contract.")
    else:
        for warning in st.session_state.get("assistant_report_warnings", ()):
            st.info(warning)
        _render_report(report_to_render, st.session_state.get("assistant_report_error"))

        st.subheader("Clause Drill-Down")
        clause_details = build_clause_detail_index(report_to_render)
        available_clause_ids = filtered_df["clause_id"].tolist()
        selected_clause_id = resolve_selected_clause_id(
            available_clause_ids,
            None,
        )
        if selected_clause_id is None:
            st.info("No clauses are available in the current filters.")
        else:
            selected_clause_id = st.selectbox(
                "Select a clause to inspect",
                options=available_clause_ids,
                index=available_clause_ids.index(selected_clause_id),
                format_func=lambda clause_id: format_clause_label(
                    clause_details.get(
                        clause_id,
                        {
                            "clause_id": clause_id,
                            "predicted_type": filtered_df.loc[
                                filtered_df["clause_id"] == clause_id, "predicted_type"
                            ].iloc[0],
                            "severity": filtered_df.loc[
                                filtered_df["clause_id"] == clause_id, "severity"
                            ].iloc[0],
                        },
                    )
                ),
            )
            selected_detail = clause_details.get(selected_clause_id)
            if selected_detail is None:
                st.info("No drill-down data is available for the selected clause.")
            else:
                detail_col1, detail_col2 = st.columns(2)
                with detail_col1:
                    st.metric("Clause", selected_detail["clause_id"])
                    st.metric("Type", selected_detail["predicted_type"])
                with detail_col2:
                    st.metric("Severity", selected_detail["severity"])
                    st.metric("Risk Score", selected_detail["risk_score"])

                st.write(selected_detail["clause_text"])
                st.write(selected_detail["explanation"] or "No explanation was available.")
                st.caption(selected_detail["supporting_reasoning"] or "Supporting reasoning unavailable.")

                if selected_detail["evidence"]:
                    st.markdown("**Supporting Evidence**")
                    for evidence in selected_detail["evidence"]:
                        st.markdown(
                            f"- **{evidence['source_title']}** "
                            f"({evidence['score']:.2f}): {evidence['snippet']}"
                        )
                else:
                    st.info("No strong supporting evidence was available for this clause.")

                if selected_detail["mitigation_action"]:
                    st.caption(f"Mitigation guidance: {selected_detail['mitigation_action']}")

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

    with st.expander("Model Explainability: Top Features by Class", expanded=False):
        try:
            features_df = top_features_by_class(model, top_n=8)
            st.dataframe(features_df, use_container_width=True)
        except ExplainabilityError as exc:
            st.info(f"Explainability unavailable: {exc}")


if __name__ == "__main__":
    render_app()
