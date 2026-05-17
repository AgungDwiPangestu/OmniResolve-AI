import pytest
from httpx import AsyncClient, ASGITransport

from src.api.main import app

@pytest.mark.asyncio
async def test_kasus_c_sofa_basah():
    """
    Kasus C: Pelanggan prioritas (CUST-001) dengan barang mahal (Sofa ORD-QHM-005) 
    rusak/basah karena kurir (terpal bocor).
    Ekspektasi: Sistem memilih 'replacement' dan memicu HITL.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/complaints",
            json={
                "message": (
                    "Sofa pesanan saya hancur dan basah semua pas sampai! "
                    "Terpal pickup kurirnya bocor katanya. Order ORD-QHM-005, Customer CUST-001."
                ),
                "session_id": "test-kasus-c-sofa-basah",
            },
        )

    assert response.status_code == 200
    data = response.json()
    
    print(f"\n[Kasus C Sofa Basah] Response: {data['response'][:200]}")
    print(f"[Kasus C Sofa Basah] Decision: {data['decision_type']}")
    print(f"[Kasus C Sofa Basah] Compensation: Rp {data.get('compensation_value_idr', 0):,.0f}")
    print(f"[Kasus C Sofa Basah] HITL Required: {data['requires_human_approval']}")
    
    assert data["session_id"] == "test-kasus-c-sofa-basah"
    assert data["decision_type"] == "replacement"
    assert data["requires_human_approval"] is True
