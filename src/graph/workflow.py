"""
src/graph/workflow.py — LangGraph State-Graph Builder

Mendefinisikan alur kerja seluruh agen:
Liaison → Auditor (dengan retry loop) → Negotiator → [HITL?] → Orchestrator
"""
import structlog
from langgraph.graph import StateGraph, END

from src.graph.state import GraphState
from src.agents.liaison_agent import liaison_agent_node
from src.agents.logistics_auditor import logistics_auditor_node, should_retry_audit
from src.agents.strategic_negotiator import strategic_negotiator_node, should_notify_supervisor
from src.agents.supply_chain_orchestrator import (
    supply_chain_orchestrator_node,
    hitl_supervisor_node,
)
from src.graph.rag_feedback import rag_feedback_node

logger = structlog.get_logger(__name__)


def build_graph() -> StateGraph:
    """
    Membangun dan mengompilasi LangGraph StateGraph.
    Dipanggil sekali saat startup aplikasi.
    """
    graph = StateGraph(GraphState)

    # --- Tambah semua node ---
    graph.add_node("liaison", liaison_agent_node)
    graph.add_node("auditor", logistics_auditor_node)
    graph.add_node("negotiator", strategic_negotiator_node)
    graph.add_node("orchestrator", supply_chain_orchestrator_node)
    graph.add_node("hitl_supervisor", hitl_supervisor_node)
    graph.add_node("rag_feedback", rag_feedback_node)

    # --- Entry point ---
    graph.set_entry_point("liaison")

    # --- Edge tetap (unconditional) ---
    graph.add_edge("liaison", "auditor")

    # --- Self-correction loop: Auditor → retry atau lanjut ---
    graph.add_conditional_edges(
        "auditor",
        should_retry_audit,
        {
            "retry_audit": "auditor",          # Loop kembali ke auditor
            "proceed_to_negotiator": "negotiator",
        },
    )

    # --- Human-in-the-Loop: Negotiator → HITL atau langsung Orchestrator ---
    graph.add_conditional_edges(
        "negotiator",
        should_notify_supervisor,
        {
            "notify_supervisor": "hitl_supervisor",
            "proceed_to_orchestrator": "orchestrator",
        },
    )

    # --- HITL → END (supervisor akan menghubungi manual, tidak ada feedback loop) ---
    graph.add_edge("hitl_supervisor", END)

    # --- Orchestrator → RAG Feedback → END ---
    graph.add_edge("orchestrator", "rag_feedback")
    graph.add_edge("rag_feedback", END)

    compiled = graph.compile()
    logger.info("workflow.compiled", nodes=list(graph.nodes.keys()))
    return compiled


# Singleton graph — dikompilasi sekali saat module di-import
_compiled_graph = None


def get_graph():
    """Lazy singleton — hanya dikompilasi saat pertama dipanggil."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
