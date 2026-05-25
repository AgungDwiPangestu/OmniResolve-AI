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

class RejectRequest(BaseModel):
    reason: str = "Permohonan tidak memenuhi syarat kompensasi berdasarkan kebijakan Qhomemart."

class ComplaintResponse(BaseModel):
    session_id: str
    response: str
    decision_type: str | None = None
    compensation_value_idr: float | None = None
    requires_human_approval: bool = False
    chain_of_thought: str | None = None


def extract_telegram_chat_id(session_id: str) -> int | None:
    """Parse chat_id dari session_id format: tg-{chat_id}-{hex}"""
    if not session_id.startswith("tg-"):
        return None
    parts = session_id.split("-")
    if len(parts) >= 2:
        try:
            return int(parts[1])
        except ValueError:
            pass
    return None


async def send_telegram_message(chat_id: int, text: str):
    """Kirim pesan Telegram ke pelanggan menggunakan Bot standalone."""
    settings = get_settings()
    if not settings.telegram_bot_token:
        logger.warning("telegram.send_skipped", reason="no token")
        return
    try:
        from telegram import Bot
        async with Bot(token=settings.telegram_bot_token) as bot:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        logger.info("telegram.hitl_notification_sent", chat_id=chat_id)
    except Exception as e:
        logger.warning("telegram.hitl_notification_failed", chat_id=chat_id, error=str(e))


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
        
        actions_taken_payload = orchestrator.get("actions_taken", [])
        # Untuk multi_choice: simpan options di actions_taken agar bisa di-fetch saat HITL disetujui
        if decision.get("decision_type") == "multi_choice" and decision.get("options"):
            actions_taken_save = {"options": decision["options"], "actions": actions_taken_payload}
        else:
            actions_taken_save = actions_taken_payload

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
            json.dumps(actions_taken_save),
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

    from src.logger import broadcast_event
    import asyncio
    broadcast_event("session_start", session_id, {"project_name": "OmniResolve-AI"})
    await asyncio.sleep(0.5)  # Race condition fix: beri waktu visualizer membuat session

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

        broadcast_event("session_end", session_id, {"project_name": "OmniResolve-AI"})

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
        broadcast_event("session_end", session_id, {"project_name": "OmniResolve-AI"})
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
    """Approval manual oleh stakeholder. Kirim notifikasi Telegram ke pelanggan + gudang."""
    settings = get_settings()
    try:
        conn = await asyncpg.connect(
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db
        )
        row = await conn.fetchrow(
            "SELECT decision_type, compensation_value_idr, order_id, actions_taken FROM complaint_sessions WHERE session_id = $1",
            session_id
        )
        await conn.execute("UPDATE complaint_sessions SET status = 'approved' WHERE session_id = $1", session_id)
        await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    chat_id = extract_telegram_chat_id(session_id)
    d_type = (row["decision_type"] or "replacement") if row else "replacement"
    value = (row["compensation_value_idr"] or 0) if row else 0
    order_id = (row["order_id"] or "-") if row else "-"

    # Ambil options dari DB (disimpan di actions_taken untuk multi_choice)
    options = []
    if row and row["actions_taken"]:
        at = row["actions_taken"]
        if isinstance(at, dict) and "options" in at:
            options = at["options"]

    # Bangun isi pesan berdasarkan decision_type
    if d_type == "replacement":
        detail = (
            "📦 *Mekanisme Penggantian Barang:*\n"
            "• Tim kami akan menghubungi Anda untuk menjadwalkan pengambilan barang yang rusak\n"
            "• Barang pengganti akan dikirim dalam 1–3 hari kerja setelah barang lama diambil"
        )
    elif d_type == "refund":
        detail = (
            f"💰 *Mekanisme Refund:*\n"
            f"• Dana sebesar *Rp {value:,.0f}* akan dikembalikan ke rekening/dompet digital Anda\n"
            f"• Proses pengembalian dana membutuhkan 3–5 hari kerja"
        )
    elif d_type == "multi_choice" and options:
        letters = ["A", "B", "C", "D"]
        opts_text = "\n".join(
            f"  *{letters[i]}.* {opt.get('label', opt.get('type', '?'))} — *Rp {opt.get('value', 0):,.0f}*"
            for i, opt in enumerate(options[:4])
        )
        detail = (
            "Karena stok produk asli tidak tersedia dalam kondisi baik, kami menawarkan pilihan kompensasi berikut:\n\n"
            f"📋 *Pilihan Anda:*\n{opts_text}\n\n"
            "Silakan balas dengan *A*, *B*, atau *C* untuk memilih."
        )
    else:
        detail = (
            f"🎟️ *Mekanisme Voucher:*\n"
            f"• Voucher senilai *Rp {value:,.0f}* akan dikirimkan ke akun belanja Anda\n"
            f"• Voucher dapat digunakan pada transaksi berikutnya di Qhomemart dalam 1×24 jam"
        )

    msg = (
        f"✅ *Keluhan Anda Telah Disetujui*\n\n"
        f"Halo! Manajemen Qhomemart telah meninjau dan *menyetujui* permohonan kompensasi Anda "
        f"untuk pesanan `{order_id}`.\n\n"
        f"{detail}\n\n"
        f"Jika ada pertanyaan, balas pesan ini atau hubungi customer service kami.\n"
        f"_Nomor referensi: `{session_id}`_"
    )

    if chat_id:
        await send_telegram_message(chat_id, msg)

        # Set session ke AWAITING_CHOICE agar bot siap terima pilihan pelanggan
        if d_type == "multi_choice":
            from src.telegram_bot.session import session_manager, ConversationStep
            sess = session_manager.get(chat_id)
            sess.step = ConversationStep.AWAITING_CHOICE
            sess.last_session_id = session_id
            sess.last_decision_type = "multi_choice"
            sess.multi_choice_options = options
            if row and row["order_id"]:
                sess.order_id = row["order_id"]

    # Kalau replacement atau multi_choice: notif gudang untuk standby
    if row and d_type in ("replacement", "multi_choice") and row["order_id"]:
        try:
            from telegram import Bot
            from src.telegram_bot.handlers import send_to_warehouse_group
            async with Bot(token=settings.telegram_bot_token) as bot:
                await send_to_warehouse_group(bot, session_id, row["order_id"])
        except Exception as e:
            logger.warning("hitl.warehouse_notify_failed", session_id=session_id, error=str(e))

    return {"message": f"Keluhan {session_id} telah DISETUJUI."}

@router.post("/complaints/reject/{session_id}")
async def reject_complaint(session_id: str, body: RejectRequest = RejectRequest()):
    """Penolakan manual oleh stakeholder. Kirim notifikasi Telegram ke pelanggan."""
    settings = get_settings()
    try:
        conn = await asyncpg.connect(
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db
        )
        row = await conn.fetchrow(
            "SELECT order_id FROM complaint_sessions WHERE session_id = $1",
            session_id
        )
        await conn.execute(
            "UPDATE complaint_sessions SET status = 'rejected', final_response = $2 WHERE session_id = $1",
            session_id, f"[DITOLAK] {body.reason}"
        )
        await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Kirim notifikasi Telegram ke pelanggan
    chat_id = extract_telegram_chat_id(session_id)
    if chat_id:
        order_id = (row["order_id"] if row else None) or "-"
        msg = (
            f"❌ *Permohonan Keluhan Tidak Dapat Disetujui*\n\n"
            f"Halo, setelah ditinjau oleh tim manajemen Qhomemart, permohonan kompensasi Anda "
            f"untuk pesanan `{order_id}` *tidak dapat kami setujui* kali ini.\n\n"
            f"📋 *Alasan:*\n_{body.reason}_\n\n"
            f"Jika Anda merasa ada kekeliruan atau ingin mengajukan pertanyaan lebih lanjut, "
            f"silakan hubungi layanan pelanggan kami.\n"
            f"_Nomor referensi: `{session_id}`_"
        )
        await send_telegram_message(chat_id, msg)

    return {"message": f"Keluhan {session_id} telah DITOLAK."}
