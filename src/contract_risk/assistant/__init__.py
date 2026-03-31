"""Agentic legal assistance helpers for Milestone 2."""

from contract_risk.assistant.corpus import LegalGuidanceRecord, load_legal_guidance_corpus
from contract_risk.assistant.explanations import ClauseExplanation, build_clause_explanation
from contract_risk.assistant.guardrails import (
    MIN_EVIDENCE_SCORE,
    STRICT_GENERATION_TEMPLATE,
    build_generation_prompt,
    evidence_is_strong,
    filter_supported_evidence,
)
from contract_risk.assistant.preprocessing import RetrievalChunk, build_retrieval_chunks
from contract_risk.assistant.reporting import (
    LEGAL_DISCLAIMER,
    REPORT_VERSION,
    build_clause_explanations,
    build_clause_references,
    build_severity_assessment,
    build_structured_report,
)
from contract_risk.assistant.retrieval import (
    LegalKnowledgeBase,
    RetrievalHit,
    RetrievalQuery,
    build_knowledge_base,
    build_retrieval_query,
    retrieve_best_practices,
    retrieve_clause_guidance,
    retrieve_contract_guidance,
    select_top_hits,
)
from contract_risk.assistant.service import generate_legal_assistance_report
from contract_risk.assistant.state import AgentState, ClausePrediction, ContractSummary, EvidenceItem, RiskFinding, WorkflowStage
from contract_risk.assistant.workflow import build_summary, complete_workflow, create_agent_state

__all__ = [
    "AgentState",
    "ClausePrediction",
    "ClauseExplanation",
    "ContractSummary",
    "EvidenceItem",
    "LegalGuidanceRecord",
    "LegalKnowledgeBase",
    "RetrievalChunk",
    "RetrievalHit",
    "RetrievalQuery",
    "RiskFinding",
    "WorkflowStage",
    "build_knowledge_base",
    "build_clause_references",
    "build_clause_explanations",
    "build_generation_prompt",
    "build_retrieval_query",
    "build_retrieval_chunks",
    "build_severity_assessment",
    "build_structured_report",
    "build_clause_explanation",
    "build_summary",
    "complete_workflow",
    "create_agent_state",
    "LEGAL_DISCLAIMER",
    "generate_legal_assistance_report",
    "MIN_EVIDENCE_SCORE",
    "STRICT_GENERATION_TEMPLATE",
    "load_legal_guidance_corpus",
    "evidence_is_strong",
    "filter_supported_evidence",
    "retrieve_best_practices",
    "retrieve_clause_guidance",
    "retrieve_contract_guidance",
    "REPORT_VERSION",
    "select_top_hits",
]
