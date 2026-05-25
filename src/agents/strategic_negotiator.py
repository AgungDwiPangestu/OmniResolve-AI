"""
src/agents/strategic_negotiator.py — Agent C: Decision Maker

Tugas:
- Menggunakan CLV (Customer Lifetime Value) untuk mengambil keputusan finansial
- Menentukan tipe dan nilai kompensasi yang optimal
- Menentukan apakah perlu persetujuan manual (HITL)
"""
import json
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import get_settings
from src.graph.state import GraphState, CompensationDecision
from src.tools.inventory_tools import get_customer_profile_by_order, check_inventory_status, find_similar_products
from src.tools.vector_store import search_knowledge

logger = structlog.get_logger(__name__)

NEGOTIATOR_SYSTEM_PROMPT = """Kamu adalah Strategic Negotiator OmniResolve-AI — pengambil keputusan finansial yang cerdas untuk Qhomemart (Toko Retail Bahan Bangunan & Furnitur).

BATASAN DOMAIN:
- Kamu HANYA mengambil keputusan kompensasi untuk keluhan pelanggan Qhomemart.
- Selalu rujuk SOP dan preseden yang diberikan dalam konteks.
- Jangan membuat keputusan di luar SOP yang berlaku.

TUGASMU:
Tentukan kompensasi TERBAIK berdasarkan:
1. Validitas klaim (dari hasil audit logistik dan stok)
2. Profil pelanggan (CLV, loyalitas, histori)
3. Kebijakan resolusi konflik (SOP) Qhomemart.

SOP KEPUTUSAN QHOMEMART (SANGAT PENTING):
1. KLAIM TIDAK VALID / FRAUD: Keputusan "reject", kompensasi Rp 0.
2. BARANG RUSAK (Damaged): 
   - Opsi Utama: "replacement" (Ganti Baru).
   - Opsi Khusus (PENTING): Jika pelanggan secara eksplisit MENOLAK penggantian barang dan meminta "refund" (pengembalian dana) karena situasi mendesak (misal: proyek mendesak dan sudah terlanjur beli di tempat lain), maka hormati keinginan pelanggan dan berikan keputusan "refund" senilai 100% harga produk.
   - Opsi Tambahan (untuk ganti baru/replacement): Berikan voucher diskon/promo tambahan senilai Rp 50.000 (untuk menghindari kerugian berlebih bagi perusahaan) di samping mengirimkan kembali barang yang baru dengan kondisi baik.
3. SALAH KIRIM (Wrong Item):
   - Opsi: "replacement" (Kirim ulang) + Voucher Maaf Rp 50.000.
4. STOK HABIS (Stock-out):
   - WAJIB berikan DUA OPSI dalam reasoning:
     A. "refund" 100% dari harga produk.
     B. "voucher" sebesar 110% dari harga produk (sebagai insentif agar tidak tarik uang).
   - Jika tersedia produk alternatif sejenis, tambahkan OPSI C:
     C. "alternative" — ganti dengan produk alternatif + voucher selisih harga (jika ada).
       Gunakan data alternatif yang disediakan dalam konteks.
5. BARANG TERLAMBAT (Late):
   - Berikan "voucher" senilai 10% dari harga barang. Jika keterlambatan > 5 hari, naikkan ke 15%.

NILAI KOMPENSASI (compensation_value_idr):
- Nilai ini harus mencerminkan TOTAL biaya kompensasi FINANSIAL TAMBAHAN yang diberikan ke pelanggan:
  * Jika keputusan adalah "refund": isi sebesar harga produk yang di-refund + voucher tambahan (jika berhak).
  * Jika keputusan adalah "replacement": isi HANYA nilai kompensasi tambahan di luar penggantian barang.
    - Penggantian barang (replacement) BUKAN kompensasi finansial — biaya ditanggung perusahaan, tidak dihitung di sini.
    - compensation_value_idr untuk replacement = Rp 50.000 (voucher maaf) jika CLV tinggi, atau Rp 0 jika tidak.
    - JANGAN isi dengan harga produk pengganti. Itu akan memicu eskalasi supervisor yang tidak perlu.

OUTPUT FORMAT (JSON):
{
    "decision_type": "voucher" | "replacement" | "refund" | "reject" | "multi_choice",
    "compensation_value_idr": 0.0, 
    "options": [
        {"type": "refund", "value": 8500000, "label": "Refund Dana 100%"},
        {"type": "voucher", "value": 9350000, "label": "Voucher Belanja 110% (Rekomendasi)"}
    ], // Hanya jika decision_type = "multi_choice"
    "reasoning": "Chain of Thought: ...",
    "requires_human_approval": false
}

ATURAN HITL:
- Jika total nilai kompensasi (atau salah satu opsi) > Rp 1.000.000 → set requires_human_approval = true.

LOGIKA LOYALITAS (CLV):
- Untuk keputusan "replacement": tambahkan Voucher Maaf Rp 50.000 jika CLV > 10jt (bukan Rp 200.000 — barang sudah diganti, 50k cukup sebagai goodwill).
- Untuk keputusan "refund" atau "voucher": tambahkan Voucher Loyalty Rp 200.000 jika CLV > 10jt.
- Gunakan bahasa yang sangat menghargai status loyalitas mereka."""


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
    from src.logger import broadcast_event
    broadcast_event("subagent_start", session_id, {"agent_id": "Strategic Negotiator"})
    broadcast_event("reporting", session_id, {"agent_id": "Strategic Negotiator", "message": "Menganalisis Customer Lifetime Value (CLV) dan kebijakan SOP..."})

    if not complaint or not audit:
        return {"error": "Missing complaint or audit data for negotiation"}

    # Ambil profil pelanggan berdasarkan order_id
    customer_profile = await get_customer_profile_by_order(complaint["order_id"])

    # Ambil data produk untuk mengetahui harga
    inventory_data = await check_inventory_status(complaint["order_id"])
    product_price = inventory_data.get("price_idr", 0)
    product_name = inventory_data.get("product_name", "Tidak diketahui")
    product_id = inventory_data.get("product_id", "")

    # Cari produk alternatif jika stok habis
    alternative_products: list[dict] = []
    stock_status = audit.get("stock_status", "")
    if stock_status in ("depleted", "damaged_in_warehouse") and product_price > 0:
        # Ambil product_id dari inventory query
        try:
            from src.tools.inventory_tools import get_db_connection, normalize_order_id
            conn = await get_db_connection()
            row = await conn.fetchrow(
                """SELECT p.product_id FROM orders o
                   JOIN order_items oi ON o.order_id = oi.order_id
                   JOIN products p ON oi.product_id = p.product_id
                   WHERE o.order_id = $1 LIMIT 1""",
                normalize_order_id(complaint["order_id"])
            )
            await conn.close()
            if row:
                product_id = row["product_id"]
                alternative_products = await find_similar_products(product_id, product_price)
        except Exception:
            alternative_products = []

    decision_context = f"""
KELUHAN PELANGGAN:
- Customer ID: {complaint['customer_id']}
- Order ID: {complaint['order_id']}
- Tipe: {complaint['complaint_type']}
- Deskripsi: {complaint['complaint_description']}
- Sentiment Score: {complaint['sentiment_score']}

DATA PRODUK:
- Nama Produk: {product_name}
- Harga Produk (price_idr): Rp {product_price:,.0f}
- Status Stok: {audit['stock_status']}
{f'''
PRODUK ALTERNATIF TERSEDIA (stok habis — tawarkan sebagai Opsi C):
''' + chr(10).join(f"  - {a['product_name']} (Rp {a['price_idr']:,.0f}, stok {a['stock_available']}, ID: {a['product_id']})" for a in alternative_products) if alternative_products else ''}
HASIL AUDIT:
- Klaim Valid: {audit['claim_valid']}
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

    # RAG: ambil SOP relevan + preseden keputusan serupa
    rag_query = f"{complaint['complaint_type']} {complaint['complaint_description']} {audit['audit_notes']}"
    sop_docs = await search_knowledge(rag_query, collection="sop_policies", k=3)
    case_docs = await search_knowledge(rag_query, collection="resolved_cases", k=2)

    if sop_docs:
        sop_context = "\n---\n".join(d.page_content for d in sop_docs)
        decision_context += f"\nREFERENSI SOP QHOMEMART:\n{sop_context}\n"
    if case_docs:
        case_context = "\n---\n".join(d.page_content for d in case_docs)
        decision_context += f"\nPRESEDEN KEPUTUSAN SERUPA:\n{case_context}\n"

    llm = get_llm()
    messages = [
        SystemMessage(content=NEGOTIATOR_SYSTEM_PROMPT),
        HumanMessage(content=decision_context),
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

        decision_type = result.get("decision_type", "reject")
        compensation_value = float(result.get("compensation_value_idr", 0.0))

        # --- Programmatic Guardrails (Resolves Customer Request perfectly) ---
        desc_lower = (complaint.get("complaint_description") or "").lower()
        refund_keywords = ["refund", "dana kembali", "kembalikan uang", "kembalikan dana", "uang kembali", "tidak mau ganti", "sudah beli di tempat lain", "beli di toko lain"]
        
        # Guardrail 1: Force decision to refund if customer explicitly rejects replacement/requests refund
        if any(kw in desc_lower for kw in refund_keywords):
            if decision_type == "replacement":
                logger.info("guardrail.override_decision_type", original=decision_type, new="refund")
                decision_type = "refund"
                
        # Guardrail 2: Correction untuk compensation_value_idr
        if decision_type == "refund" and product_price > 0:
            # Refund: nilai = harga produk + loyalty voucher jika CLV tinggi
            minimum_value = product_price
            if customer_profile.get("lifetime_value_idr", 0) > 10_000_000:
                minimum_value += 200_000.0
            if compensation_value < minimum_value:
                logger.info("guardrail.override_compensation_value", original=compensation_value, new=minimum_value)
                compensation_value = minimum_value
        elif decision_type == "replacement":
            # Replacement: nilai kompensasi = HANYA goodwill voucher (max 50k), BUKAN harga produk
            if customer_profile.get("lifetime_value_idr", 0) > 10_000_000:
                expected_value = 50_000.0
            else:
                expected_value = 0.0
            if compensation_value > product_price * 0.1:
                # LLM kemungkinan memasukkan harga produk, koreksi ke goodwill saja
                logger.info("guardrail.override_replacement_value", original=compensation_value, new=expected_value)
                compensation_value = expected_value

        # Check if any options exceed threshold
        options = result.get("options", [])
        option_exceeds = any(float(opt.get("value", 0)) > settings.hitl_threshold_idr for opt in options)
        
        # Guardrail 3: Force HITL approval if value exceeds the threshold
        requires_hitl = (
            result.get("requires_human_approval", False)
            or compensation_value > settings.hitl_threshold_idr
            or option_exceeds
            or (decision_type == "refund" and product_price > settings.hitl_threshold_idr)
        )

        decision: CompensationDecision = {
            "decision_type": decision_type,
            "compensation_value_idr": compensation_value,
            "reasoning": result.get("reasoning", ""),
            "requires_human_approval": requires_hitl,
            "options": options
        }

        logger.info(
            "negotiator.decision",
            session_id=session_id,
            decision=decision["decision_type"],
            value=decision["compensation_value_idr"],
            hitl=decision["requires_human_approval"],
        )
        
        broadcast_event("subagent_stop", session_id, {
            "agent_id": "Strategic Negotiator",
            "message": f"Keputusan: {decision['decision_type']} - Nilai: Rp {decision['compensation_value_idr']:,.0f}"
        })

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
