"""
tests/test_compensation_paths.py — Test Jalur Keputusan Kompensasi

Menguji ke-4 jalur keputusan yang bisa diambil Strategic Negotiator:
1. Refund / Replacement → pelanggan setia, barang hilang
2. Voucher → pelanggan baru, barang murah, keluhan ringan
3. Reject → klaim subjektif, pelanggan baru sekali

Setiap test menggunakan assertion FLEKSIBEL karena output LLM non-deterministic.
Strategi: assert pada boundary logic, bukan exact LLM output.

Jalankan: pytest tests/test_compensation_paths.py -v
"""
import pytest


# ============================================================================
# Skenario 1: Refund/Replacement Path — Barang Hilang, Pelanggan Setia
# ============================================================================
@pytest.mark.asyncio
async def test_jalur_refund_barang_hilang_pelanggan_setia(async_client):
    """
    Pelanggan setia (CUST-001, CLV 15jt, 23 pesanan) melaporkan
    barang hilang (ORD-001, Lemari Rp 2.5jt).

    Ekspektasi:
    - Klaim valid → decision bukan "reject"
    - Pelanggan setia + barang mahal → "replacement" atau "refund"
    - Pipeline selesai tanpa error
    """
    response = await async_client.post(
        "/api/v1/complaints",
        json={
            "message": (
                "Paket lemari saya (ORD-001) tidak pernah sampai! "
                "Sudah 2 minggu saya menunggu dan tidak ada kabar dari kurir. "
                "Ini sangat mengecewakan. Customer ID: CUST-001."
            ),
            "session_id": "test-refund-001",
        },
    )

    assert response.status_code == 200, f"Pipeline error: {response.text}"
    data = response.json()

    print(f"\n{'='*60}")
    print(f"[Refund Path] Session: {data['session_id']}")
    print(f"[Refund Path] Response: {data['response'][:200]}")
    print(f"[Refund Path] Decision: {data['decision_type']}")
    print(f"[Refund Path] Kompensasi: Rp {data.get('compensation_value_idr', 0):,.0f}")
    print(f"[Refund Path] HITL: {data['requires_human_approval']}")
    print(f"{'='*60}")

    # Assertions
    assert data["session_id"] == "test-refund-001"
    assert data["response"] is not None
    assert len(data["response"]) > 20, "Response terlalu pendek"

    # Pelanggan setia + klaim valid → TIDAK boleh ditolak
    assert data["decision_type"] != "reject", (
        f"Pelanggan setia dengan klaim valid seharusnya tidak ditolak, "
        f"tapi dapat: {data['decision_type']}"
    )

    # Decision type harus salah satu opsi yang valid
    assert data["decision_type"] in {"voucher", "replacement", "refund"}, (
        f"Decision type tidak valid: {data['decision_type']}"
    )


# ============================================================================
# Skenario 2: Voucher Path — Pengiriman Terlambat, Pelanggan Baru
# ============================================================================
@pytest.mark.asyncio
async def test_jalur_voucher_pelanggan_baru_barang_murah(async_client):
    """
    Pelanggan baru (CUST-002, CLV 250K, 2 pesanan) mengeluh
    pengiriman terlambat untuk barang murah (ORD-003, Rak Rp 350K).

    Ekspektasi:
    - Pelanggan baru + barang murah → kompensasi konservatif (voucher)
    - Tidak memicu HITL (kompensasi kecil)
    """
    response = await async_client.post(
        "/api/v1/complaints",
        json={
            "message": (
                "Pengiriman rak dinding saya (ORD-003) sudah 1 minggu "
                "belum sampai juga. Kapan ini dikirim? "
                "Customer ID: CUST-002."
            ),
            "session_id": "test-voucher-001",
        },
    )

    assert response.status_code == 200, f"Pipeline error: {response.text}"
    data = response.json()

    print(f"\n{'='*60}")
    print(f"[Voucher Path] Session: {data['session_id']}")
    print(f"[Voucher Path] Response: {data['response'][:200]}")
    print(f"[Voucher Path] Decision: {data['decision_type']}")
    print(f"[Voucher Path] Kompensasi: Rp {data.get('compensation_value_idr', 0):,.0f}")
    print(f"[Voucher Path] HITL: {data['requires_human_approval']}")
    print(f"{'='*60}")

    # Assertions
    assert data["session_id"] == "test-voucher-001"
    assert data["response"] is not None

    # Pelanggan baru + barang murah → kompensasi harus konservatif
    if data["decision_type"] == "voucher":
        # Jika voucher, nilainya harus masuk akal untuk barang Rp 350K
        assert data.get("compensation_value_idr", 0) <= 500_000, (
            f"Voucher terlalu besar untuk barang Rp 350K: "
            f"Rp {data.get('compensation_value_idr', 0):,.0f}"
        )

    # Kompensasi kecil → TIDAK boleh memicu HITL
    if data.get("compensation_value_idr", 0) <= 1_000_000:
        assert data["requires_human_approval"] is False, (
            "Kompensasi di bawah Rp 1.000.000 tidak seharusnya memerlukan approval supervisor"
        )


# ============================================================================
# Skenario 3: Reject Path — Klaim Subjektif, Pelanggan Baru Sekali
# ============================================================================
@pytest.mark.asyncio
async def test_jalur_reject_klaim_subjektif(async_client):
    """
    Pelanggan baru sekali (CUST-999, CLV 0, 1 pesanan) mengeluh
    dengan alasan subjektif tanpa bukti kerusakan nyata.

    Ekspektasi:
    - LLM kemungkinan reject atau beri voucher kecil
    - Tidak boleh memberi refund/replacement untuk klaim tidak jelas
    - Tidak memicu HITL
    """
    response = await async_client.post(
        "/api/v1/complaints",
        json={
            "message": (
                "Saya tidak suka barangnya. Menurut saya kualitasnya jelek. "
                "Saya mau refund. Order ORD-003, Customer CUST-999."
            ),
            "session_id": "test-reject-001",
        },
    )

    assert response.status_code == 200, f"Pipeline error: {response.text}"
    data = response.json()

    print(f"\n{'='*60}")
    print(f"[Reject Path] Session: {data['session_id']}")
    print(f"[Reject Path] Response: {data['response'][:200]}")
    print(f"[Reject Path] Decision: {data['decision_type']}")
    print(f"[Reject Path] Kompensasi: Rp {data.get('compensation_value_idr', 0):,.0f}")
    print(f"[Reject Path] HITL: {data['requires_human_approval']}")
    print(f"[Reject Path] CoT: {data.get('chain_of_thought', '')[:300]}")
    print(f"{'='*60}")

    # Assertions
    assert data["session_id"] == "test-reject-001"
    assert data["response"] is not None

    # Decision type harus valid
    assert data["decision_type"] in {"voucher", "replacement", "refund", "reject"}, (
        f"Decision type tidak valid: {data['decision_type']}"
    )

    # Klaim subjektif → seharusnya BUKAN refund penuh
    # (LLM mungkin memberi voucher kecil atau reject, keduanya OK)
    if data["decision_type"] == "refund":
        # Jika entah kenapa refund, nilainya harus sangat kecil
        assert data.get("compensation_value_idr", 0) < 350_000, (
            "Refund penuh untuk klaim subjektif tanpa bukti seharusnya tidak terjadi"
        )

    # Tidak boleh memicu HITL untuk kasus klaim kecil
    assert data["requires_human_approval"] is False, (
        "Klaim subjektif dari pelanggan baru tidak seharusnya memerlukan supervisor"
    )
