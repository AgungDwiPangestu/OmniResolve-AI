"""
tests/test_scenarios.py — Demo Scenarios untuk Kompetisi

Dua skenario utama yang disiapkan untuk demo kepada juri:
- Kasus A: Pelanggan baru, barang murah → voucher
- Kasus B: Pelanggan setia, barang mahal rusak → replacement + kurir

Jalankan: pytest tests/ -v
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

from src.api.main import app


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_health_check():
    """Pastikan service sehat sebelum demo."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "OmniResolve-AI"


@pytest.mark.asyncio
async def test_kasus_a_pelanggan_baru():
    """
    Kasus A: Skenario Qhomemart - Barang murah salah warna.
    Ekspektasi: sistem memilih kompensasi konservatif (voucher).
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/complaints",
            json={
                "message": (
                    "Halo Qhomemart, saya beli Cat Dulux (Order ORD-QHM-003) kok warnanya salah? "
                    "Pesan putih datang kuning. Saya CUST-002."
                ),
                "session_id": "test-kasus-a-001",
            },
        )

    assert response.status_code == 200
    data = response.json()
    print(f"\n[Kasus A] Response: {data['response'][:200]}")
    print(f"[Kasus A] Decision: {data['decision_type']}")
    print(f"[Kasus A] Compensation: Rp {data.get('compensation_value_idr', 0):,.0f}")

    assert data["session_id"] == "test-kasus-a-001"
    assert data["response"] is not None
    assert data["requires_human_approval"] is False


@pytest.mark.asyncio
async def test_kasus_b_pelanggan_setia():
    """
    Kasus B: Skenario Qhomemart - Barang mahal rusak saat dikirim.
    Ekspektasi: sistem memilih penggantian barang atau refund, dan butuh HITL Supervisor.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/complaints",
            json={
                "message": (
                    "Sofa pesanan saya hancur dan basah semua pas sampai! "
                    "Terpal pickup kurirnya bocor katanya. Minta ganti baru sekarang juga! "
                    "Order ORD-QHM-005, Customer CUST-001."
                ),
                "session_id": "test-kasus-b-001",
            },
        )

    assert response.status_code == 200
    data = response.json()
    print(f"\n[Kasus B] Response: {data['response'][:200]}")
    print(f"[Kasus B] Decision: {data['decision_type']}")
    print(f"[Kasus B] Compensation: Rp {data.get('compensation_value_idr', 0):,.0f}")
    print(f"[Kasus B] HITL Required: {data['requires_human_approval']}")
    print(f"[Kasus B] CoT: {data.get('chain_of_thought', '')[:300]}")

    assert data["session_id"] == "test-kasus-b-001"
    assert data["response"] is not None
    # Pelanggan setia dengan barang mahal → harusnya bukan reject
    assert data["decision_type"] != "reject"


@pytest.mark.asyncio
async def test_chat_openai_compatible():
    """
    Test OpenAI-compatible endpoint untuk claude-office.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/completions",
            json={
                "model": "omni-resolve-ai",
                "messages": [
                    {"role": "user", "content": "Barang saya tidak sampai sudah 2 minggu. Order ORD-001."}
                ],
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"
    assert len(data["choices"]) > 0
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert len(data["choices"][0]["message"]["content"]) > 10
    print(f"\n[Chat] Response: {data['choices'][0]['message']['content'][:300]}")
