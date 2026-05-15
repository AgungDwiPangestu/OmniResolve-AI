"""
src/agents/logistics_auditor.py — Agent B: Deep Research

Tugas:
- Verifikasi silang data internal (CCTV metadata, histori kurir, laporan stok)
- Menentukan validitas klaim secara objektif
- Jika data kurang, meminta Negotiator untuk loop kembali (self-correction)
"""
import json
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import get_settings
from src.graph.state import GraphState, AuditResult
from src.tools.inventory_tools import check_inventory_status
from src.tools.courier_tools import get_courier_log

logger = structlog.get_logger(__name__)

MAX_AUDIT_RETRIES = 3

AUDITOR_SYSTEM_PROMPT = """Kamu adalah Logistics & Inventory Auditor OmniResolve-AI.

TUGASMU:
1. Analisis data audit yang diberikan (stok, kurir, CCTV metadata)
2. Tentukan apakah klaim pelanggan VALID, TIDAK VALID, atau BUTUH DATA LEBIH
3. Berikan ringkasan objektif dari temuan audit

OUTPUT FORMAT (JSON):
{
    "claim_valid": true | false | null,
    "stock_status": "available" | "depleted" | "damaged_in_warehouse",
    "courier_log_summary": "...",
    "cctv_metadata_summary": "...",
    "audit_notes": "...",
    "need_more_data": false,
    "additional_data_needed": "..."  // Hanya jika need_more_data=true
}

PENTING: Bersikaplah OBJEKTIF. Jangan berpihak ke pelanggan maupun perusahaan."""


def get_llm():
    settings = get_settings()
    return ChatOpenAI(
        model=settings.llm_model_name,
        openai_api_key=settings.llm_api_key,
        openai_api_base=settings.llm_base_url,
        temperature=0.1,  # Low temperature untuk reasoning yang lebih deterministic
    )


async def logistics_auditor_node(state: GraphState) -> dict:
    """
    Node Logistics Auditor dalam LangGraph workflow.
    Dipanggil setelah Liaison Agent mengumpulkan data komplain.
    """
    session_id = state["session_id"]
    complaint = state.get("complaint")
    retry_count = state.get("audit_retry_count", 0)

    logger.info("auditor.start", session_id=session_id, retry=retry_count)

    if not complaint:
        return {"audit_result": None, "error": "No complaint data to audit"}

    # Ambil data dari mock tools
    inventory_data = await check_inventory_status(complaint["order_id"])
    courier_log = await get_courier_log(complaint["order_id"])

    audit_context = f"""
DATA AUDIT untuk Order ID: {complaint['order_id']}
Customer ID: {complaint['customer_id']}
Tipe Komplain: {complaint['complaint_type']}
Deskripsi: {complaint['complaint_description']}

DATA STOK:
{json.dumps(inventory_data, indent=2, ensure_ascii=False)}

LOG KURIR:
{json.dumps(courier_log, indent=2, ensure_ascii=False)}

CCTV Metadata (simulasi):
- Timestamp terakhir scan gudang: 2026-05-10 14:23:00
- Status kondisi paket saat keluar gudang: "OK"
- Nama petugas gudang: "Budi Santoso"
"""

    llm = get_llm()
    messages = [
        SystemMessage(content=AUDITOR_SYSTEM_PROMPT),
        HumanMessage(content=audit_context),
    ]

    try:
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        result = json.loads(content)

        audit_result: AuditResult = {
            "claim_valid": result.get("claim_valid"),
            "stock_status": result.get("stock_status", "unknown"),
            "courier_log_summary": result.get("courier_log_summary", ""),
            "cctv_metadata_summary": result.get("cctv_metadata_summary", ""),
            "audit_notes": result.get("audit_notes", ""),
        }

        logger.info(
            "auditor.done",
            session_id=session_id,
            claim_valid=audit_result["claim_valid"],
            need_more_data=result.get("need_more_data", False),
        )

        return {
            "audit_result": audit_result,
            "audit_retry_count": retry_count + 1,
            "messages": [response],
        }

    except (json.JSONDecodeError, KeyError) as e:
        logger.error("auditor.parse_error", error=str(e))
        fallback: AuditResult = {
            "claim_valid": None,
            "stock_status": "unknown",
            "courier_log_summary": "Audit error — data tidak tersedia",
            "cctv_metadata_summary": "N/A",
            "audit_notes": f"Parse error: {e}",
        }
        return {"audit_result": fallback, "audit_retry_count": retry_count + 1}


def should_retry_audit(state: GraphState) -> str:
    """
    Routing function — menentukan apakah audit perlu diulang (self-correction).
    Return: "retry_audit" | "proceed_to_negotiator"
    """
    audit = state.get("audit_result")
    retry_count = state.get("audit_retry_count", 0)

    # Jika audit belum conclusive dan masih bisa retry
    if audit and audit["claim_valid"] is None and retry_count < MAX_AUDIT_RETRIES:
        logger.info("auditor.retry", retry_count=retry_count)
        return "retry_audit"

    return "proceed_to_negotiator"
