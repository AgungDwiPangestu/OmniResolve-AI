"""
src/telegram_bot/bot.py — Telegram Bot Application

Entry point untuk bot. Support dua mode:
- polling: untuk development lokal (tidak butuh domain publik)
- webhook: untuk production di SumoPod (lebih efisien, zero polling)

CARA PAKAI:
  Polling (lokal):  python -m src.telegram_bot.bot
  Webhook (prod):   Otomatis dideteksi dari TELEGRAM_MODE=webhook
"""
import asyncio
import structlog
from telegram import BotCommand

from src.logger import setup_logging
setup_logging()

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from src.config import get_settings
from src.telegram_bot.handlers import (
    cmd_start,
    cmd_help,
    cmd_status,
    cmd_cancel,
    cmd_faq,
    cmd_human,
    cmd_register_warehouse,
    cmd_register_courier,
    handle_text,
    handle_photo,
    handle_callback,
)

logger = structlog.get_logger(__name__)


def build_application() -> Application:
    """Bangun Telegram Application dengan semua handler terdaftar."""
    settings = get_settings()

    if not settings.telegram_bot_token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN belum diset di .env! "
            "Dapatkan token dari @BotFather di Telegram."
        )

    app = Application.builder().token(settings.telegram_bot_token).build()

    # --- Command handlers ---
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("faq", cmd_faq))
    app.add_handler(CommandHandler("human", cmd_human))
    
    # --- Gudang & Kurir Group Registration handlers ---
    app.add_handler(CommandHandler("register_warehouse", cmd_register_warehouse))
    app.add_handler(CommandHandler("register_gudang", cmd_register_warehouse))
    app.add_handler(CommandHandler("register_courier", cmd_register_courier))
    app.add_handler(CommandHandler("register_kurir", cmd_register_courier))

    # --- Message handlers ---
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # --- Callback query (inline keyboard) ---
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("telegram.bot_built", mode=settings.telegram_mode)
    return app


async def setup_bot_commands(app: Application):
    """Set command list yang muncul di menu Telegram."""
    commands = [
        BotCommand("start", "Mulai komplain baru"),
        BotCommand("status", "Cek status komplain"),
        BotCommand("cancel", "Batalkan proses komplain saat ini"),
        BotCommand("faq", "Pusat bantuan otomatis"),
        BotCommand("human", "Panggil CS Manusia"),
        BotCommand("help", "Bantuan penggunaan"),
    ]
    await app.bot.set_my_commands(commands)
    logger.info("telegram.commands_set")


async def run_polling():
    """
    Jalankan bot dalam mode polling (lokal/dev).
    Tidak butuh domain publik atau SSL.
    """
    settings = get_settings()
    app = build_application()

    logger.info(
        "telegram.polling_start",
        bot_token_preview=settings.telegram_bot_token[:10] + "...",
    )

    async with app:
        await setup_bot_commands(app)
        await app.updater.start_polling(
            drop_pending_updates=True,  # Abaikan pesan lama saat restart
            allowed_updates=["message", "callback_query"],
        )
        await app.start()
        logger.info("telegram.polling_running", msg="Bot berjalan! Ctrl+C untuk stop.")

        # Tetap running sampai di-interrupt
        await asyncio.Event().wait()

        await app.updater.stop()
        await app.stop()


async def run_webhook(webhook_url: str):
    """
    Jalankan bot dalam mode webhook (production SumoPod).
    Telegram akan push update ke URL kita, lebih efisien dari polling.
    """
    app = build_application()
    settings = get_settings()

    webhook_path = "/api/v1/telegram/webhook"
    full_webhook_url = f"{webhook_url.rstrip('/')}{webhook_path}"

    logger.info("telegram.webhook_start", url=full_webhook_url)

    async with app:
        await setup_bot_commands(app)
        await app.bot.set_webhook(
            url=full_webhook_url,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
        logger.info("telegram.webhook_registered")
        # Webhook dihandle oleh FastAPI router (lihat src/api/routers/telegram_webhook.py)


def get_ptb_application() -> Application:
    """
    Expose PTB Application instance untuk integrasi dengan FastAPI webhook.
    Dipanggil dari FastAPI startup event.
    """
    return build_application()


if __name__ == "__main__":
    """Jalankan langsung untuk mode polling (development)."""
    import sys
    settings = get_settings()

    if settings.telegram_mode == "webhook" and settings.telegram_webhook_url:
        asyncio.run(run_webhook(settings.telegram_webhook_url))
    else:
        asyncio.run(run_polling())
