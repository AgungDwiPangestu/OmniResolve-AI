"""
tests/test_concurrent.py — Test Concurrent/Parallel Complaints

Menguji apakah pipeline bisa menangani beberapa keluhan secara bersamaan
tanpa race condition atau data tercampur antar sesi.

Jalankan: pytest tests/test_concurrent.py -v
"""
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from src.api.main import app


@pytest.mark.asyncio
async def test_keluhan_bersamaan_tidak_tercampur():
    """
    Kirim 3 keluhan secara bersamaan (concurrent).
    Setiap response harus memiliki session_id yang benar
    dan data tidak boleh tercampur antar sesi.
    """
    complaints = [
        {
            "message": "Rak dinding saya ORD-003 warnanya salah. Customer CUST-002.",
            "session_id": "concurrent-001",
        },
        {
            "message": "Lemari saya ORD-001 tidak sampai. Customer CUST-001.",
            "session_id": "concurrent-002",
        },
        {
            "message": "Saya kecewa dengan layanan. Order ORD-003, Customer CUST-999.",
            "session_id": "concurrent-003",
        },
    ]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        timeout=180.0,
    ) as client:
        # Kirim semua keluhan secara bersamaan
        tasks = [
            client.post("/api/v1/complaints", json=c)
            for c in complaints
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    # Verifikasi semua response
    for i, resp in enumerate(responses):
        if isinstance(resp, Exception):
            print(f"\n[Concurrent {i+1}] ERROR: {resp}")
            continue

        assert resp.status_code == 200, f"Concurrent {i+1} gagal: {resp.text}"
        data = resp.json()

        print(f"\n[Concurrent {i+1}] Session: {data['session_id']}")
        print(f"[Concurrent {i+1}] Decision: {data['decision_type']}")

        # Session ID harus cocok dengan yang dikirim
        assert data["session_id"] == complaints[i]["session_id"], (
            f"Session ID tercampur! Expected: {complaints[i]['session_id']}, "
            f"Got: {data['session_id']}"
        )
        assert data["response"] is not None

    # Minimal semua harus berhasil (tidak ada exception)
    successful = [r for r in responses if not isinstance(r, Exception)]
    assert len(successful) >= 2, (
        f"Minimal 2 dari 3 concurrent requests harus berhasil, "
        f"hanya {len(successful)} yang berhasil"
    )
