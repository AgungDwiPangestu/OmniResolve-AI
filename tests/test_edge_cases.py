"""
tests/test_edge_cases.py — Test Edge Cases & Error Handling

Menguji skenario batas:
1. Order & Customer tidak dikenal → fallback mock data
2. Stok habis → trigger Purchase Order
3. Input minimal / ambigu → pipeline tetap jalan
4. Input sangat panjang

Jalankan: pytest tests/test_edge_cases.py -v
"""
import pytest


@pytest.mark.asyncio
async def test_order_dan_customer_tidak_dikenal(async_client):
    """Order/Customer ID tidak ada di mock → pipeline tetap jalan."""
    response = await async_client.post(
        "/api/v1/complaints",
        json={
            "message": (
                "Barang saya hilang! Order ORD-999, Customer CUST-UNKNOWN."
            ),
            "session_id": "test-unknown-001",
        },
    )

    assert response.status_code == 200
    data = response.json()

    print(f"\n[Unknown Data] Decision: {data['decision_type']}")
    print(f"[Unknown Data] Response: {data['response'][:200]}")

    assert data["session_id"] == "test-unknown-001"
    assert data["response"] is not None
    assert len(data["response"]) > 10

    if data["decision_type"] is not None:
        assert data["decision_type"] in {"voucher", "replacement", "refund", "reject"}


@pytest.mark.asyncio
async def test_stok_habis_trigger_purchase_order(async_client):
    """ORD-002 stok=0 (depleted). Pipeline tetap jalan, mungkin trigger PO."""
    response = await async_client.post(
        "/api/v1/complaints",
        json={
            "message": (
                "Meja makan saya (ORD-002) salah warna. "
                "Saya pelanggan setia, minta ganti. Customer ID: CUST-001."
            ),
            "session_id": "test-stok-habis-001",
        },
    )

    assert response.status_code == 200
    data = response.json()

    print(f"\n[Stok Habis] Decision: {data['decision_type']}")
    print(f"[Stok Habis] Kompensasi: Rp {data.get('compensation_value_idr', 0):,.0f}")
    print(f"[Stok Habis] Response: {data['response'][:250]}")

    assert data["response"] is not None
    assert data["decision_type"] != "reject"
    assert data["decision_type"] in {"voucher", "replacement", "refund"}


@pytest.mark.asyncio
async def test_input_minimal_tanpa_identitas(async_client):
    """Input tanpa Order/Customer ID → Liaison fallback, pipeline tidak crash."""
    response = await async_client.post(
        "/api/v1/complaints",
        json={
            "message": "Saya kecewa dengan pesanan saya. Barangnya jelek.",
            "session_id": "test-minimal-001",
        },
    )

    assert response.status_code == 200
    data = response.json()

    print(f"\n[Input Minimal] Decision: {data['decision_type']}")
    print(f"[Input Minimal] Response: {data['response'][:200]}")

    assert data["session_id"] == "test-minimal-001"
    assert data["response"] is not None
    assert len(data["response"]) > 0


@pytest.mark.asyncio
async def test_input_sangat_panjang(async_client):
    """Input >1000 chars. Pipeline harus tetap bisa proses."""
    keluhan = ("Saya sangat kecewa dengan pelayanan toko ini. " * 20)
    keluhan += " Order saya ORD-001, Customer CUST-001."

    response = await async_client.post(
        "/api/v1/complaints",
        json={"message": keluhan, "session_id": "test-panjang-001"},
    )

    assert response.status_code == 200
    data = response.json()

    print(f"\n[Input Panjang] Input length: {len(keluhan)} chars")
    print(f"[Input Panjang] Decision: {data['decision_type']}")

    assert data["response"] is not None
    assert len(data["response"]) > 10
