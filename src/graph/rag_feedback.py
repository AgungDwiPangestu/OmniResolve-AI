"""
src/graph/rag_feedback.py — Post-Resolution Knowledge Feedback Node

Node LangGraph yang berjalan setelah Supply Chain Orchestrator selesai.
Tugasnya: auto-ingest kasus yang baru diselesaikan ke knowledge base
sehingga sistem terus belajar dari setiap interaksi nyata.

Posisi dalam workflow:
  orchestrator → rag_feedback → END
  hitl_supervisor → END  (kasus HITL tidak di-ingest, menunggu approval manusia)
"""
import structlog
from src.graph.state import GraphState
from src.tools.knowledge_ingestion import ingest_resolved_case

logger = structlog.get_logger(__name__)


async def rag_feedback_node(state: GraphState) -> dict:
    """
    Node terakhir setelah orchestrator — simpan kasus ke knowledge base.
    Error di sini tidak menghentikan workflow (silent fail by design).
    """
    session_id = state.get("session_id", "unknown")
    logger.info("rag_feedback.start", session_id=session_id)

    try:
        success = await ingest_resolved_case(state)
        if success:
            logger.info("rag_feedback.done", session_id=session_id, status="ingested")
        else:
            logger.info("rag_feedback.done", session_id=session_id, status="skipped")
    except Exception as e:
        # Jangan crash pipeline utama hanya karena feedback gagal
        logger.warning("rag_feedback.error", session_id=session_id, error=str(e))

    return {}
