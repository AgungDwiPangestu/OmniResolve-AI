"""
src/api/routers/telegram_webhook.py — Telegram Webhook Endpoint

Di production (SumoPod), Telegram mengirim update ke endpoint ini.
Di development, bot berjalan dengan polling (tidak perlu endpoint ini aktif).

Endpoint ini diregistrasi di FastAPI sebagai route:
POST /api/v1/telegram/webhook
"""
import structlog
from fastapi import APIRouter, Request, Response, HTTPException
from telegram import Update

from src.config import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()

# PTB Application instance — diset saat startup FastAPI
_ptb_app = None


def set_ptb_app(app):
    """Dipanggil dari FastAPI lifespan untuk inject PTB app instance."""
    global _ptb_app
    _ptb_app = app


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    Endpoint webhook untuk Telegram.
    Telegram akan POST setiap update ke sini ketika mode=webhook.

    Setup di production:
    1. Set TELEGRAM_MODE=webhook di .env SumoPod
    2. Set TELEGRAM_WEBHOOK_URL=https://your-domain.sumopod.com
    3. Bot otomatis register webhook saat startup
    """
    settings = get_settings()

    if settings.telegram_mode != "webhook":
        raise HTTPException(
            status_code=400,
            detail="Bot berjalan dalam mode polling, bukan webhook."
        )

    if _ptb_app is None:
        raise HTTPException(status_code=503, detail="Telegram bot belum diinisialisasi")

    try:
        data = await request.json()
        update = Update.de_json(data, _ptb_app.bot)
        await _ptb_app.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error("telegram.webhook_error", error=str(e))
        # Return 200 agar Telegram tidak retry terus-menerus
        return Response(status_code=200)


@router.get("/telegram/info")
async def telegram_bot_info():
    """Cek info dan status bot."""
    settings = get_settings()
    if not settings.telegram_bot_token:
        return {"status": "not_configured", "message": "TELEGRAM_BOT_TOKEN belum diset"}

    if _ptb_app is None:
        return {"status": "not_initialized"}

    try:
        bot_info = await _ptb_app.bot.get_me()
        return {
            "status": "running",
            "mode": settings.telegram_mode,
            "bot_username": f"@{bot_info.username}",
            "bot_name": bot_info.full_name,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
