"""
src/tools/knowledge_ingestion.py — Knowledge Base Ingestion Pipeline

Modul ini bertanggung jawab untuk:

1. AUTO-INGEST (Feedback Loop):
   Setelah setiap kasus komplain diselesaikan oleh pipeline, hasilnya otomatis
   disimpan sebagai "resolved case" ke collection `resolved_cases`.
   Ini adalah mekanisme "pembelajaran berkelanjutan" — knowledge base tumbuh
   secara organik dari setiap interaksi nyata.

2. MANUAL INGEST (Admin):
   Admin/developer dapat menambahkan dokumen baru ke collection mana saja
   melalui endpoint API atau fungsi seed.

3. SEED AWAL:
   Saat pertama kali setup, jalankan seed_initial_knowledge() untuk mengisi
   semua collection dengan data dasar (SOP, FAQ, katalog produk).

ALUR PEMBELAJARAN:
  Komplain masuk → Pipeline berjalan → Kasus selesai
       ↓
  ingest_resolved_case() dipanggil
       ↓
  Kasus disimpan ke collection `resolved_cases`
       ↓
  Kasus berikutnya: agen retrieve preseden yang relevan dari `resolved_cases`
       ↓
  LLM mendapat konteks lebih kaya → keputusan lebih akurat
"""
import structlog
from datetime import datetime, timezone

from src.tools.vector_store import ingest_documents, SEED_SOP_POLICIES, SEED_FAQ_PATTERNS, SEED_PRODUCT_CATALOG

logger = structlog.get_logger(__name__)


async def ingest_resolved_case(state: dict) -> bool:
    """
    Auto-ingest kasus yang baru selesai diproses ke collection `resolved_cases`.

    Dipanggil oleh rag_feedback_node setelah supply_chain_orchestrator selesai.
    Kasus yang di-ingest menjadi referensi preseden untuk kasus serupa di masa depan.

    Args:
        state: GraphState lengkap setelah pipeline selesai

    Returns:
        True jika berhasil di-ingest, False jika ada error atau data tidak cukup
    """
    complaint = state.get("complaint")
    audit = state.get("audit_result")
    decision = state.get("compensation_decision")
    profile = state.get("customer_profile")
    session_id = state.get("session_id", "unknown")

    # Tidak ingest jika data tidak lengkap
    if not complaint or not audit or not decision:
        logger.warning("rag_feedback.skip", reason="incomplete_state", session_id=session_id)
        return False

    # Bangun ringkasan kasus yang informatif untuk LLM
    loyalty_info = ""
    if profile:
        clv = profile.get("lifetime_value_idr", 0)
        loyalty_info = (
            f"Profil pelanggan: CLV Rp {clv:,.0f}, "
            f"setia={profile.get('is_loyal', False)}, "
            f"total_order={profile.get('total_orders', 0)}"
        )

    case_summary = f"""KASUS DISELESAIKAN — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

Tipe Komplain: {complaint.get('complaint_type', 'unknown')}
Deskripsi: {complaint.get('complaint_description', '')}
{loyalty_info}

Hasil Audit:
- Klaim Valid: {audit.get('claim_valid')}
- Status Stok: {audit.get('stock_status', 'unknown')}
- Catatan Audit: {audit.get('audit_notes', '')}

Keputusan Akhir:
- Tipe: {decision.get('decision_type', 'unknown')}
- Nilai Kompensasi: Rp {decision.get('compensation_value_idr', 0):,.0f}
- Reasoning: {decision.get('reasoning', '')[:400]}"""

    doc = {
        "content": case_summary,
        "metadata": {
            "session_id": session_id,
            "complaint_type": complaint.get("complaint_type", "unknown"),
            "decision_type": decision.get("decision_type", "unknown"),
            "claim_valid": str(audit.get("claim_valid")),
            "stock_status": audit.get("stock_status", "unknown"),
            "compensation_value": decision.get("compensation_value_idr", 0),
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        },
    }

    count = await ingest_documents([doc], collection="resolved_cases")
    if count > 0:
        logger.info(
            "rag_feedback.ingested",
            session_id=session_id,
            decision_type=decision.get("decision_type"),
            complaint_type=complaint.get("complaint_type"),
        )
        return True

    return False


async def seed_initial_knowledge() -> dict[str, int]:
    """
    Seed semua collection dengan data awal.

    Dipanggil melalui: POST /api/v1/admin/knowledge/seed
    Aman dijalankan berulang kali — dokumen yang sama akan di-ingest ulang
    (langchain_postgres tidak de-duplikasi by default).

    Returns:
        Dict jumlah dokumen yang di-ingest per collection
        Contoh: {"sop_policies": 7, "faq_patterns": 5, "product_catalog": 3, "resolved_cases": 0}
    """
    results: dict[str, int] = {}

    logger.info("seed.start")

    results["sop_policies"] = await ingest_documents(SEED_SOP_POLICIES, collection="sop_policies")
    logger.info("seed.sop_policies_done", count=results["sop_policies"])

    results["faq_patterns"] = await ingest_documents(SEED_FAQ_PATTERNS, collection="faq_patterns")
    logger.info("seed.faq_patterns_done", count=results["faq_patterns"])

    results["product_catalog"] = await ingest_documents(SEED_PRODUCT_CATALOG, collection="product_catalog")
    logger.info("seed.product_catalog_done", count=results["product_catalog"])

    # resolved_cases dimulai kosong — akan terisi otomatis dari feedback loop
    results["resolved_cases"] = 0

    logger.info("seed.complete", total=sum(results.values()), breakdown=results)
    return results


async def ingest_manual_documents(documents: list[dict], collection: str) -> int:
    """
    Ingest dokumen secara manual ke collection tertentu.
    Wrapper untuk dipakai oleh admin API endpoint.

    Args:
        documents: List dict dengan key 'content' dan optional 'metadata'
        collection: Target collection (sop_policies / faq_patterns / product_catalog / resolved_cases)

    Returns:
        Jumlah dokumen yang berhasil di-ingest
    """
    count = await ingest_documents(documents, collection=collection)
    logger.info("manual_ingest.done", collection=collection, count=count)
    return count
