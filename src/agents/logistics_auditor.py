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

AUDITOR_SYSTEM_PROMPT = """Kamu adalah Logistics & Inventory Auditor OmniResolve-AI (Enterprise Fraud-Prevention Level).

TUGASMU:
1. Analisis data audit yang diberikan (stok, kurir, CCTV metadata).
2. Lakukan CROSS-CHECK antara cerita pelanggan vs bukti logistik internal.
3. Tentukan apakah klaim pelanggan VALID atau TIDAK VALID (FRAUD).
4. Berikan ringkasan objektif dari temuan audit.

PANDUAN VALIDASI BERDASARKAN TIPE KELUHAN:

A. BARANG RUSAK (damaged_item):
   - Jika kurir MELAPORKAN kerusakan (damage_reported_by_courier=true) atau status pengiriman "delivered_with_damage_report" → klaim VALID.
   - Jika CCTV mencatat barang sudah rusak di gudang (warehouse_condition="damaged_in_warehouse") → klaim VALID.
   - Jika kurir melaporkan barang utuh DAN CCTV mencatat barang OK saat keluar gudang → klaim TIDAK VALID (indikasi fraud).

B. BARANG TIDAK SESUAI / SALAH KIRIM (wrong_item):
   - Jika barang sudah terkirim (ada log kurir) dan pelanggan mengeluh salah produk → klaim VALID (kesalahan gudang).

C. BARANG KURANG (missing_item / partial delivery):
   - Jika ada catatan pengiriman parsial atau jumlah tidak sesuai → klaim VALID.

D. BARANG TERLAMBAT (late_delivery):
   - Jika tanggal pengiriman terakhir di log kurir menunjukkan keterlambatan signifikan → klaim VALID.

E. STOK HABIS SETELAH BAYAR (stock-out):
   - Jika stok di database = 0 dan warehouse_condition = "depleted" → klaim VALID.
   - Tidak ada log kurir adalah WAJAR karena barang memang belum pernah dikirim.
   - JANGAN tolak klaim hanya karena tidak ada data pengiriman.

F. FRAUD / ORDER TIDAK DIKENAL:
   - Jika order ID menghasilkan "Produk Tidak Dikenal" → klaim TIDAK VALID.
   - Jika pelanggan mengklaim kerusakan TETAPI semua bukti logistik menyatakan barang utuh → TIDAK VALID.

OUTPUT FORMAT (JSON):
{
    "claim_valid": true | false | null,
    "stock_status": "available" | "depleted" | "damaged_in_warehouse",
    "courier_log_summary": "...",
    "cctv_metadata_summary": "...",
    "audit_notes": "...",
    "need_more_data": false,
    "additional_data_needed": "..."
}

PENTING: Bersikaplah OBJEKTIF. Validasi berdasarkan BUKTI, bukan asumsi."""


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
    from src.logger import broadcast_event
    broadcast_event("subagent_start", session_id, {"agent_id": "Logistics Auditor"})
    broadcast_event("reporting", session_id, {"agent_id": "Logistics Auditor", "message": "Memeriksa log kurir dan CCTV metadata untuk verifikasi klaim..."})

    if not complaint:
        return {"audit_result": None, "error": "No complaint data to audit"}

    # Ambil data dari tools
    inventory_data = await check_inventory_status(complaint["order_id"])
    courier_log = await get_courier_log(complaint["order_id"])

    # Generate CCTV metadata berdasarkan kondisi gudang aktual
    wh_condition = inventory_data.get("warehouse_condition", "unknown")
    if wh_condition == "good":
        cctv_summary = (
            "CCTV Metadata Gudang:\n"
            "- Timestamp scan terakhir: 2026-05-10 14:23:00\n"
            "- Status kondisi paket saat keluar gudang: BAIK / OK\n"
            "- Petugas gudang: Budi Santoso\n"
            "- Catatan: Paket dikemas sesuai SOP, tidak ada kerusakan terdeteksi"
        )
    elif wh_condition == "damaged_in_warehouse":
        cctv_summary = (
            "CCTV Metadata Gudang:\n"
            "- Timestamp scan terakhir: 2026-05-10 14:23:00\n"
            "- Status kondisi paket saat keluar gudang: ADA KERUSAKAN TERCATAT\n"
            "- Petugas gudang: Budi Santoso\n"
            "- Catatan: Barang terdeteksi memiliki cacat/kerusakan sejak di gudang sebelum dikirim"
        )
    elif wh_condition == "depleted":
        cctv_summary = (
            "CCTV Metadata Gudang:\n"
            "- TIDAK ADA REKAMAN — barang tidak pernah diproses keluar gudang\n"
            "- Alasan: Stok habis (depleted), barang belum pernah dikirimkan\n"
            "- Catatan: Order ini berstatus 'dibayar' tapi belum bisa diproses karena stok kosong"
        )
    else:
        cctv_summary = (
            "CCTV Metadata Gudang:\n"
            "- Status: DATA TIDAK TERSEDIA\n"
            "- Catatan: Order ID tidak dikenali dalam sistem gudang"
        )

    audit_context = f"""
DATA AUDIT untuk Order ID: {complaint['order_id']}
Customer ID: {complaint['customer_id']}
Tipe Komplain: {complaint['complaint_type']}
Deskripsi: {complaint['complaint_description']}

DATA STOK & PRODUK:
{json.dumps(inventory_data, indent=2, ensure_ascii=False)}

LOG KURIR / PENGIRIMAN:
{json.dumps(courier_log, indent=2, ensure_ascii=False)}

{cctv_summary}
"""

    llm = get_llm()
    messages = [
        SystemMessage(content=AUDITOR_SYSTEM_PROMPT),
        HumanMessage(content=audit_context),
    ]

    try:
        response = await llm.ainvoke(messages)
        
        raw_content = response.content.strip()
        if raw_content.startswith("```json"):
            raw_content = raw_content[7:]
        elif raw_content.startswith("```"):
            raw_content = raw_content[3:]
        if raw_content.endswith("```"):
            raw_content = raw_content[:-3]
            
        result = json.loads(raw_content.strip())

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
        
        broadcast_event("subagent_stop", session_id, {
            "agent_id": "Logistics Auditor",
            "message": f"Klaim Valid: {audit_result['claim_valid']}. {audit_result['audit_notes']}"
        })

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
