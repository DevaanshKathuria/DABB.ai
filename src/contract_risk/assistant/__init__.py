"""Agentic legal assistance helpers for Milestone 2."""

from contract_risk.assistant.corpus import LegalGuidanceRecord, load_legal_guidance_corpus
from contract_risk.assistant.preprocessing import RetrievalChunk, build_retrieval_chunks
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
    "build_retrieval_query",
    "build_retrieval_chunks",
    "build_summary",
    "complete_workflow",
    "create_agent_state",
    "generate_legal_assistance_report",
    "load_legal_guidance_corpus",
    "retrieve_best_practices",
    "retrieve_clause_guidance",
    "retrieve_contract_guidance",
    "select_top_hits",
]
