"""
src/agents/supply_chain_orchestrator.py — Agent D: Action Taker

Tugas:
- Eksekutor akhir yang menjalankan aksi nyata berdasarkan keputusan Negotiator
- Melakukan API Call ke sistem ERP, kurir, atau men-trigger Purchase Order
- Menyusun final response yang dikirim kembali ke pelanggan via Liaison
"""
import json
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import get_settings
from src.graph.state import GraphState, OrchestratorAction
from src.tools.erp_tools import update_erp_stock, trigger_purchase_order
from src.tools.courier_tools import dispatch_courier

logger = structlog.get_logger(__name__)

RESPONSE_COMPOSER_PROMPT = """Kamu adalah Response Composer OmniResolve-AI.
Susun pesan AKHIR yang akan dikirimkan kepada pelanggan.

Pesan harus:
- Empatik dan profesional
- Menjelaskan dengan JELAS apa yang akan dilakukan perusahaan
- Memberikan perkiraan waktu penyelesaian
- Tidak menggunakan bahasa teknis/jargon
- Menggunakan Bahasa Indonesia yang natural

Format: Plain text, bukan JSON."""


def get_llm():
    settings = get_settings()
    return ChatOpenAI(
        model=settings.llm_model_name,
        openai_api_key=settings.llm_api_key,
        openai_api_base=settings.llm_base_url,
        temperature=0.4,  # Sedikit lebih kreatif untuk response yang natural
    )


async def supply_chain_orchestrator_node(state: GraphState) -> dict:
    """
    Node Supply Chain Orchestrator dalam LangGraph workflow.
    """
    session_id = state["session_id"]
    decision = state.get("compensation_decision")
    complaint = state.get("complaint")

    logger.info("orchestrator.start", session_id=session_id)

    if not decision or not complaint:
        return {"error": "Missing decision or complaint for orchestration"}

    actions_taken = []
    actions_failed = []
    erp_status = "not_triggered"
    courier_status = "not_triggered"
    po_triggered = False

    # --- Eksekusi aksi berdasarkan tipe keputusan ---
    if decision["decision_type"] == "replacement":
        # Update stok di ERP + dispatch kurir pengganti
        erp_result = await update_erp_stock(complaint["order_id"], action="reserve_replacement")
        if erp_result["success"]:
            actions_taken.append(f"Stok pengganti dipesan di ERP: {erp_result['message']}")
            erp_status = "updated"
        else:
            actions_failed.append(f"ERP update gagal: {erp_result['message']}")
            # Self-correction: Coba trigger PO jika stok habis
            po_result = await trigger_purchase_order(complaint["order_id"])
            if po_result["success"]:
                actions_taken.append(f"Purchase Order ke supplier di-trigger: {po_result['message']}")
                po_triggered = True
            else:
                actions_failed.append(f"PO gagal: {po_result['message']}")

        courier_result = await dispatch_courier(
            order_id=complaint["order_id"],
            action="pickup_and_deliver",
        )
        if courier_result["success"]:
            actions_taken.append(f"Kurir pengganti dijadwalkan: {courier_result['message']}")
            courier_status = "dispatched"
        else:
            actions_failed.append(f"Dispatch kurir gagal: {courier_result['message']}")

    elif decision["decision_type"] == "voucher":
        actions_taken.append(
            f"Voucher diskon Rp {decision['compensation_value_idr']:,.0f} diterbitkan"
        )
        erp_status = "voucher_issued"

    elif decision["decision_type"] == "refund":
        erp_result = await update_erp_stock(complaint["order_id"], action="process_refund")
        if erp_result["success"]:
            actions_taken.append(f"Proses refund diinisiasi: {erp_result['message']}")
            erp_status = "refund_initiated"
        else:
            actions_failed.append(f"Refund gagal: {erp_result['message']}")

    elif decision["decision_type"] == "reject":
        actions_taken.append("Klaim ditolak — surat penjelasan disiapkan untuk pelanggan")

    orchestrator_action: OrchestratorAction = {
        "actions_taken": actions_taken,
        "actions_failed": actions_failed,
        "erp_update_status": erp_status,
        "courier_dispatch_status": courier_status,
        "po_triggered": po_triggered,
    }

    # --- Compose final response untuk pelanggan ---
    response_context = f"""
Keputusan: {decision['decision_type']}
Nilai kompensasi: Rp {decision['compensation_value_idr']:,.0f}
Aksi berhasil: {', '.join(actions_taken) if actions_taken else 'tidak ada'}
Aksi gagal: {', '.join(actions_failed) if actions_failed else 'tidak ada'}
Reasoning: {decision['reasoning']}
"""

    llm = get_llm()
    messages = [
        SystemMessage(content=RESPONSE_COMPOSER_PROMPT),
        HumanMessage(content=response_context),
    ]

    try:
        response = await llm.ainvoke(messages)
        final_response = response.content

        logger.info(
            "orchestrator.done",
            session_id=session_id,
            actions_taken=len(actions_taken),
            actions_failed=len(actions_failed),
        )

        return {
            "orchestrator_action": orchestrator_action,
            "final_response": final_response,
            "messages": [response],
        }

    except Exception as e:
        logger.error("orchestrator.response_error", error=str(e))
        return {
            "orchestrator_action": orchestrator_action,
            "final_response": f"Keluhan Anda telah kami proses. Tim kami akan menghubungi Anda segera. (Ref: {session_id})",
        }


async def hitl_supervisor_node(state: GraphState) -> dict:
    """
    Node HITL — mengirim notifikasi ke supervisor untuk approval manual.
    Dipanggil ketika kompensasi melebihi threshold.
    """
    import httpx
    settings = get_settings()
    decision = state.get("compensation_decision")
    session_id = state["session_id"]

    logger.info(
        "hitl.triggered",
        session_id=session_id,
        value=decision["compensation_value_idr"] if decision else 0,
    )

    # Mock notifikasi supervisor (Slack webhook / email)
    payload = {
        "text": (
            f"⚠️ *APPROVAL REQUIRED* — OmniResolve-AI\n"
            f"Session: `{session_id}`\n"
            f"Keputusan: `{decision['decision_type'] if decision else 'unknown'}`\n"
            f"Nilai: Rp {decision['compensation_value_idr']:,.0f if decision else 0}\n"
            f"Reasoning: {decision['reasoning'][:200] if decision else '-'}..."
        )
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(settings.supervisor_webhook_url, json=payload)
        logger.info("hitl.notification_sent", session_id=session_id)
    except Exception as e:
        logger.warning("hitl.notification_failed", error=str(e))

    # Setelah notifikasi, tetap lanjut ke orchestrator (dengan flag sudah dinotif)
    return {
        "final_response": (
            "Keluhan Anda memerlukan persetujuan dari tim senior kami. "
            "Kami akan menghubungi Anda dalam waktu 1x24 jam. "
            f"Nomor referensi: {session_id}"
        )
    }
