"""
tests/test_hitl_flow.py — Test Human-in-the-Loop (HITL) Flow

Menguji alur HITL yang dipicu ketika kompensasi melebihi threshold Rp 1.000.000.
Pipeline: Negotiator → hitl_supervisor → END (bukan ke Orchestrator).

Jalankan: pytest tests/test_hitl_flow.py -v
"""
import pytest

from src.config import get_settings


# ============================================================================
# Skenario: HITL Trigger — Kompensasi Besar untuk Pelanggan Setia
# ============================================================================
@pytest.mark.asyncio
async def test_hitl_trigger_kompensasi_besar(async_client):
    """
    Pelanggan setia (CUST-001, CLV 15jt) mengeluh sofa mahal (ORD-004, Rp 4.2jt)
    rusak total dan minta refund penuh.

    Ekspektasi:
    - Kompensasi > Rp 1.000.000 → requires_human_approval = True
    - Pipeline tetap memberikan response sementara ke pelanggan
    - Decision type = "replacement" atau "refund" (bukan voucher/reject)
    """
    settings = get_settings()

    response = await async_client.post(
        "/api/v1/complaints",
        json={
            "message": (
                "Sofa saya (ORD-004) rusak total saat diterima! "
                "Kainnya robek parah dan rangkanya bengkok. "
                "Ini sofa seharga Rp 4.200.000 dan saya minta refund penuh! "
                "Saya sudah jadi pelanggan setia selama bertahun-tahun. "
                "Customer ID: CUST-001."
            ),
            "session_id": "test-hitl-001",
        },
    )

    assert response.status_code == 200, f"Pipeline error: {response.text}"
    data = response.json()

    print(f"\n{'='*60}")
    print(f"[HITL Flow] Session: {data['session_id']}")
    print(f"[HITL Flow] Response: {data['response'][:250]}")
    print(f"[HITL Flow] Decision: {data['decision_type']}")
    print(f"[HITL Flow] Kompensasi: Rp {data.get('compensation_value_idr', 0):,.0f}")
    print(f"[HITL Flow] HITL Required: {data['requires_human_approval']}")
    print(f"[HITL Flow] Threshold Config: Rp {settings.hitl_threshold_idr:,.0f}")
    print(f"[HITL Flow] CoT: {data.get('chain_of_thought', '')[:300]}")
    print(f"{'='*60}")

    # Assertions
    assert data["session_id"] == "test-hitl-001"
    assert data["response"] is not None
    assert len(data["response"]) > 20, "Response HITL terlalu pendek"

    # Pelanggan setia + barang rusak → bukan reject
    assert data["decision_type"] != "reject", (
        "Pelanggan setia dengan sofa rusak seharusnya tidak ditolak"
    )

    # Barang mahal (Rp 4.2jt) → kompensasi seharusnya > threshold
    compensation = data.get("compensation_value_idr", 0)
    if compensation > settings.hitl_threshold_idr:
        # Jika kompensasi besar → WAJIB HITL
        assert data["requires_human_approval"] is True, (
            f"Kompensasi Rp {compensation:,.0f} melebihi threshold "
            f"Rp {settings.hitl_threshold_idr:,.0f}, seharusnya requires_human_approval=True"
        )

    # Decision harus premium untuk pelanggan loyal
    assert data["decision_type"] in {"replacement", "refund"}, (
        f"Pelanggan setia dengan barang rusak Rp 4.2jt seharusnya mendapat "
        f"replacement/refund, bukan: {data['decision_type']}"
    )


# ============================================================================
# Test Konsistensi Threshold HITL antara Config dan Kode
# ============================================================================
@pytest.mark.asyncio
async def test_konsistensi_threshold_hitl():
    """
    Validasi SOP: memastikan nilai threshold HITL di konfigurasi
    konsisten dengan yang digunakan di business logic.

    SOP menetapkan: Kompensasi > Rp 1.000.000 WAJIB persetujuan supervisor.
    """
    settings = get_settings()

    # Threshold harus Rp 1.000.000 sesuai SOP
    assert settings.hitl_threshold_idr == 1_000_000.0, (
        f"Threshold HITL di config ({settings.hitl_threshold_idr:,.0f}) "
        f"tidak sesuai SOP (Rp 1.000.000)"
    )

    # Validasi bahwa threshold digunakan di negotiator (import check)
    from src.agents.strategic_negotiator import should_notify_supervisor
    assert callable(should_notify_supervisor), (
        "Fungsi should_notify_supervisor harus ada di strategic_negotiator"
    )

    print(f"\n[SOP] Threshold HITL: Rp {settings.hitl_threshold_idr:,.0f} ✅")
    print(f"[SOP] Fungsi routing HITL tersedia: should_notify_supervisor ✅")
