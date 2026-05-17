"""
src/api/routers/complaints.py — Complaint API Endpoints

Endpoint utama untuk menerima dan memproses keluhan pelanggan.
"""
import uuid
import json
import asyncpg
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.graph.workflow import get_graph
from src.graph.state import GraphState
from src.config import get_settings

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


async def save_session_to_db(session_id: str, raw_input: str, state: GraphState):
    settings = get_settings()
    try:
        conn = await asyncpg.connect(
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db
        )
        
        complaint = state.get("complaint") or {}
        audit = state.get("audit_result") or {}
        decision = state.get("compensation_decision") or {}
        orchestrator = state.get("orchestrator_action") or {}
        
        query = """
            INSERT INTO complaint_sessions (
                session_id, raw_input, customer_id, order_id, complaint_type,
                sentiment_score, claim_valid, stock_status, audit_notes,
                decision_type, compensation_value_idr, requires_human_approval,
                chain_of_thought, actions_taken, actions_failed, final_response, status
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17
            )
            ON CONFLICT (session_id) DO UPDATE SET
                final_response = EXCLUDED.final_response,
                status = EXCLUDED.status,
                updated_at = NOW()
        """
        
        status = "pending_hitl" if decision.get("requires_human_approval") else "completed"
        
        await conn.execute(
            query,
            session_id,
            raw_input,
            complaint.get("customer_id"),
            complaint.get("order_id"),
            complaint.get("complaint_type"),
            complaint.get("sentiment_score"),
            audit.get("claim_valid"),
            audit.get("stock_status"),
            audit.get("audit_notes"),
            decision.get("decision_type"),
            decision.get("compensation_value_idr"),
            decision.get("requires_human_approval", False),
            decision.get("reasoning"),
            json.dumps(orchestrator.get("actions_taken", [])),
            json.dumps(orchestrator.get("actions_failed", [])),
            state.get("final_response"),
            status
        )
        await conn.close()
    except Exception as e:
        logger.error("db.save_session_error", session_id=session_id, error=str(e))


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
        
        # Simpan ke tabel complaint_sessions sebagai history/log nyata
        await save_session_to_db(session_id, request.message, final_state)

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

# --- NEW ENDPOINTS FOR ADMIN DASHBOARD ---

@router.get("/complaints/logs")
async def get_complaint_logs():
    """Ambil histori seluruh komplain untuk dashboard admin."""
    settings = get_settings()
    try:
        conn = await asyncpg.connect(
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db
        )
        rows = await conn.fetch("SELECT * FROM complaint_sessions ORDER BY created_at DESC LIMIT 50")
        await conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/complaints/detail/{session_id}")
async def get_complaint_detail(session_id: str):
    """Ambil rincian spesifik satu komplain untuk modal approval."""
    settings = get_settings()
    try:
        conn = await asyncpg.connect(
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db
        )
        row = await conn.fetchrow("""
            SELECT cs.*, c.customer_name 
            FROM complaint_sessions cs
            LEFT JOIN customers c ON cs.customer_id = c.customer_id
            WHERE cs.session_id = $1
        """, session_id)
        await conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        return dict(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/complaints/approve/{session_id}")
async def approve_complaint(session_id: str):
    """Approval manual oleh stakeholder."""
    settings = get_settings()
    try:
        conn = await asyncpg.connect(
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db
        )
        # 1. Update status di DB
        await conn.execute("UPDATE complaint_sessions SET status = 'approved' WHERE session_id = $1", session_id)
        
        # 2. Trigger Orchestrator Logic (Update ERP, dsb) secara manual
        # Di sini kita bisa panggil node orchestrator secara mandiri jika perlu
        
        await conn.close()
        return {"message": f"Keluhan {session_id} telah DISETUJUI dan diproses ke ERP."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/complaints/reject/{session_id}")
async def reject_complaint(session_id: str):
    """Penolakan manual oleh stakeholder."""
    settings = get_settings()
    try:
        conn = await asyncpg.connect(
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db
        )
        await conn.execute("UPDATE complaint_sessions SET status = 'rejected' WHERE session_id = $1", session_id)
        await conn.close()
        return {"message": f"Keluhan {session_id} telah DITOLAK."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
