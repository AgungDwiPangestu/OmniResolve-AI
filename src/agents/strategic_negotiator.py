"""
src/agents/strategic_negotiator.py — Agent C: Decision Maker

Tugas:
- Menggunakan CLV (Customer Lifetime Value) untuk mengambil keputusan finansial
- Menentukan tipe dan nilai kompensasi yang optimal
- Mentrigger Human-in-the-Loop jika nilai kompensasi melebihi threshold
"""
import json
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import get_settings
from src.graph.state import GraphState, CompensationDecision
from src.tools.inventory_tools import get_customer_profile_mock

logger = structlog.get_logger(__name__)

NEGOTIATOR_SYSTEM_PROMPT = """Kamu adalah Strategic Negotiator OmniResolve-AI — pengambil keputusan finansial yang cerdas untuk Qhomemart (Toko Retail Bahan Bangunan & Furnitur).

TUGASMU:
Tentukan kompensasi TERBAIK berdasarkan:
1. Validitas klaim (dari hasil audit logistik dan stok)
2. Profil pelanggan (CLV, loyalitas, histori)
3. Kebijakan resolusi konflik (SOP) Qhomemart.

SOP KEPUTUSAN QHOMEMART (SANGAT PENTING):
1. BARANG RUSAK SAAT PENGIRIMAN (Contoh: Sofa basah, Kloset pecah, Keramik retak):
   - Keputusan: "replacement" (Ganti Baru).
   - Wajib ganti baru jika klaim valid karena kesalahan kurir/cuaca. TIDAK BOLEH hanya memberikan voucher untuk barang rusak fisik.
   
2. BARANG TIDAK SESUAI PESANAN / SALAH KIRIM (Contoh: Salah warna cat, salah ukuran granit):
   - Keputusan: "replacement" (Kirim ulang barang yang benar dan tarik yang salah).
   - Tambahkan kompensasi dana ke `compensation_value_idr` (misal Rp 50.000 - Rp 100.000) sebagai bentuk permintaan maaf (voucher ekstra).
   
3. BARANG KURANG (PARTIAL DELIVERY) (Contoh: Beli 10 dus granit, hanya sampai 9 dus):
   - Keputusan: "replacement" (Kirim sisa barang yang kurang).
   
4. BARANG TERLAMBAT DATANG (Late Delivery):
   - Keputusan: "voucher" (Voucher gratis ongkir / diskon). Besaran tergantung harga barang dan CLV pelanggan.
   
5. STOK HABIS (OUT OF STOCK) SETELAH PEMBAYARAN:
   - Jika stok di database `depleted` atau kosong -> Keputusan: "refund" (Uang kembali penuh).
   
6. KLAIM TIDAK VALID / FRAUD (Contoh: Kurir lapor utuh, tapi pelanggan komplain rusak tanpa bukti atau rusak karena pemakaian sendiri):
   - Keputusan: "reject" (Tolak dengan penjelasan sopan dan tawarkan layanan perbaikan berbayar atau panduan garansi).

OUTPUT FORMAT (JSON):
{
    "decision_type": "voucher" | "replacement" | "refund" | "reject",
    "compensation_value_idr": 0.0, // Isi > 0 jika "voucher" ATAU jika memberikan kompensasi ekstra pada saat "replacement"
    "reasoning": "Chain of Thought: ...",
    "requires_human_approval": false
}

LOGIKA CLV & HITL:
- Pelanggan setia (is_loyal=true atau lifetime_value > 5jt): Berikan nilai voucher ekstra yang lebih tinggi.
- Nilai barang yang di-replacement ATAU nilai refund ATAU nilai voucher > Rp 1.000.000 WAJIB requires_human_approval = true"""


def get_llm():
    settings = get_settings()
    return ChatOpenAI(
        model=settings.llm_model_name,
        openai_api_key=settings.llm_api_key,
        openai_api_base=settings.llm_base_url,
        temperature=0.2,
    )


async def strategic_negotiator_node(state: GraphState) -> dict:
    """
    Node Strategic Negotiator dalam LangGraph workflow.
    """
    session_id = state["session_id"]
    complaint = state.get("complaint")
    audit = state.get("audit_result")
    settings = get_settings()

    logger.info("negotiator.start", session_id=session_id)

    if not complaint or not audit:
        return {"error": "Missing complaint or audit data for negotiation"}

    # Ambil profil pelanggan
    customer_profile = await get_customer_profile_mock(complaint["customer_id"])

    decision_context = f"""
KELUHAN PELANGGAN:
- Customer ID: {complaint['customer_id']}
- Order ID: {complaint['order_id']}
- Tipe: {complaint['complaint_type']}
- Deskripsi: {complaint['complaint_description']}
- Sentiment Score: {complaint['sentiment_score']}

HASIL AUDIT:
- Klaim Valid: {audit['claim_valid']}
- Status Stok: {audit['stock_status']}
- Log Kurir: {audit['courier_log_summary']}
- Catatan Audit: {audit['audit_notes']}

PROFIL PELANGGAN (CLV):
- Nama: {customer_profile['customer_name']}
- Pelanggan Setia: {customer_profile['is_loyal']}
- Customer Lifetime Value: Rp {customer_profile['lifetime_value_idr']:,.0f}
- Total Pesanan: {customer_profile['total_orders']}
- Komplain Sebelumnya: {customer_profile['previous_complaints']}

BATAS HITL: Rp {settings.hitl_threshold_idr:,.0f}
"""

    llm = get_llm()
    messages = [
        SystemMessage(content=NEGOTIATOR_SYSTEM_PROMPT),
        HumanMessage(content=decision_context),
    ]

    try:
        response = await llm.ainvoke(messages)
        result = json.loads(response.content)

        compensation_value = float(result.get("compensation_value_idr", 0.0))
        requires_hitl = (
            result.get("requires_human_approval", False)
            or compensation_value > settings.hitl_threshold_idr
        )

        decision: CompensationDecision = {
            "decision_type": result.get("decision_type", "reject"),
            "compensation_value_idr": compensation_value,
            "reasoning": result.get("reasoning", ""),
            "requires_human_approval": requires_hitl,
        }

        logger.info(
            "negotiator.decision",
            session_id=session_id,
            decision=decision["decision_type"],
            value=decision["compensation_value_idr"],
            hitl=decision["requires_human_approval"],
        )

        return {
            "customer_profile": customer_profile,
            "compensation_decision": decision,
            "messages": [response],
        }

    except (json.JSONDecodeError, KeyError) as e:
        logger.error("negotiator.parse_error", error=str(e))
        fallback: CompensationDecision = {
            "decision_type": "voucher",
            "compensation_value_idr": 50_000.0,
            "reasoning": f"Fallback decision due to parse error: {e}",
            "requires_human_approval": False,
        }
        return {"compensation_decision": fallback}


def should_notify_supervisor(state: GraphState) -> str:
    """
    Routing function — apakah perlu notifikasi supervisor (HITL).
    Return: "notify_supervisor" | "proceed_to_orchestrator"
    """
    decision = state.get("compensation_decision")
    if decision and decision["requires_human_approval"]:
        logger.info("negotiator.hitl_triggered", value=decision["compensation_value_idr"])
        return "notify_supervisor"
    return "proceed_to_orchestrator"
