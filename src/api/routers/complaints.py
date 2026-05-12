"""
src/api/routers/complaints.py — Complaint API Endpoints

Endpoint utama untuk menerima dan memproses keluhan pelanggan.
"""
import uuid
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.graph.workflow import get_graph
from src.graph.state import GraphState

logger = structlog.get_logger(__name__)
router = APIRouter()


class ComplaintRequest(BaseModel):
    message: str
    session_id: str | None = None


class ComplaintResponse(BaseModel):
    session_id: str
    response: str
    decision_type: str | None = None
    compensation_value_idr: float | None = None
    requires_human_approval: bool = False
    chain_of_thought: str | None = None


@router.post("/complaints", response_model=ComplaintResponse)
async def submit_complaint(request: ComplaintRequest):
    """
    Submit keluhan pelanggan ke pipeline Multi-Agent.

    Alur: Liaison → Auditor (loop jika perlu) → Negotiator → [HITL?] → Orchestrator
    """
    session_id = request.session_id or str(uuid.uuid4())
    logger.info("complaint.received", session_id=session_id, message_len=len(request.message))

    initial_state: GraphState = {
        "messages": [],
        "raw_input": request.message,
        "complaint": None,
        "audit_result": None,
        "audit_retry_count": 0,
        "customer_profile": None,
        "compensation_decision": None,
        "orchestrator_action": None,
        "final_response": None,
        "session_id": session_id,
        "error": None,
    }

    try:
        graph = get_graph()
        final_state = await graph.ainvoke(initial_state)

        decision = final_state.get("compensation_decision")

        return ComplaintResponse(
            session_id=session_id,
            response=final_state.get("final_response") or "Keluhan Anda sedang diproses.",
            decision_type=decision["decision_type"] if decision else None,
            compensation_value_idr=decision["compensation_value_idr"] if decision else None,
            requires_human_approval=decision["requires_human_approval"] if decision else False,
            chain_of_thought=decision["reasoning"] if decision else None,
        )

    except Exception as e:
        logger.error("complaint.pipeline_error", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline error: {str(e)}",
        )
