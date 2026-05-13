"""
tests/test_telegram_endpoint.py — Test Telegram Webhook & Info Endpoints

Menguji endpoint Telegram yang tersedia di FastAPI:
- GET /api/v1/telegram/info → cek status bot
- POST /api/v1/telegram/webhook → webhook mode validation

Jalankan: pytest tests/test_telegram_endpoint.py -v
"""
import pytest


@pytest.mark.asyncio
async def test_telegram_info_endpoint(async_client):
    """GET /api/v1/telegram/info → mengembalikan status bot."""
    response = await async_client.get("/api/v1/telegram/info")

    assert response.status_code == 200
    data = response.json()

    print(f"\n[Telegram Info] Status: {data.get('status')}")
    print(f"[Telegram Info] Data: {data}")

    # Status harus ada (bisa "not_configured", "not_initialized", "running", "error")
    assert "status" in data


@pytest.mark.asyncio
async def test_telegram_webhook_saat_polling_mode(async_client):
    """
    POST /api/v1/telegram/webhook saat mode=polling → harus return 400.
    Karena di development, bot jalan dengan polling, bukan webhook.
    """
    response = await async_client.post(
        "/api/v1/telegram/webhook",
        json={"update_id": 123456789, "message": {"text": "test"}},
    )

    # Di polling mode, webhook endpoint seharusnya menolak
    # Bisa 400 (mode salah) atau 503 (bot belum init)
    assert response.status_code in {400, 503}, (
        f"Webhook saat polling mode seharusnya ditolak, tapi dapat: {response.status_code}"
    )

    print(f"\n[Telegram Webhook] Status: {response.status_code}")
    print(f"[Telegram Webhook] Response: {response.json()}")
