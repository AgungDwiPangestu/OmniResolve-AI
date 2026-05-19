"""
src/api/main.py — FastAPI Application Entry Point

Expose endpoints yang kompatibel dengan OpenAI API format
sehingga bisa langsung dihubungkan ke claude-office atau frontend manapun.

Juga mengatur lifecycle Telegram bot:
- Mode polling: bot dijalankan sebagai background task
- Mode webhook: bot diregistrasi ke Telegram saat startup
"""
import asyncio
import structlog
from contextlib import asynccontextmanager

from src.logger import setup_logging
setup_logging()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.api.routers import complaints, health, chat, telegram_webhook, diagnostic

logger = structlog.get_logger(__name__)
settings = get_settings()

# Background task handle untuk polling mode
_polling_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Setup dan teardown saat aplikasi start/stop."""
    global _polling_task

    logger.info(
        "api.startup",
        environment=settings.environment,
        model=settings.llm_model_name,
        telegram_mode=settings.telegram_mode if settings.telegram_bot_token else "disabled",
    )

    # --- Setup Telegram Bot ---
    if settings.telegram_bot_token:
        try:
            from src.telegram_bot.bot import get_ptb_application, run_polling, run_webhook
            ptb_app = get_ptb_application()

            # Inject instance ke webhook router
            telegram_webhook.set_ptb_app(ptb_app)

            if settings.telegram_mode == "polling":
                # Jalankan polling sebagai asyncio background task
                _polling_task = asyncio.create_task(run_polling())
                logger.info("telegram.polling_task_started")

            elif settings.telegram_mode == "webhook" and settings.telegram_webhook_url:
                # Register webhook ke Telegram
                await run_webhook(settings.telegram_webhook_url)
                logger.info("telegram.webhook_registered")

        except Exception as e:
            logger.error("telegram.startup_error", error=str(e))
            # Jangan crash FastAPI jika bot gagal start
    else:
        logger.warning("telegram.disabled", reason="TELEGRAM_BOT_TOKEN not set")

    yield  # Application berjalan di sini

    # --- Teardown ---
    if _polling_task and not _polling_task.done():
        _polling_task.cancel()
        try:
            await _polling_task
        except asyncio.CancelledError:
            pass
        logger.info("telegram.polling_stopped")

    logger.info("api.shutdown")


app = FastAPI(
    title="OmniResolve-AI",
    description=(
        "Autonomous Omni-Channel Retail Concierge & Conflict Resolver. "
        "Sistem Multi-Agent untuk automasi resolusi konflik pelanggan berbasis ReAct + LangGraph. "
        "Interface pelanggan: Telegram Bot."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — izinkan akses dari claude-office atau frontend manapun
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Batasi di production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Routers
app.include_router(health.router, tags=["System"])
app.include_router(complaints.router, prefix="/api/v1", tags=["Complaints"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat (OpenAI-compatible)"])
app.include_router(telegram_webhook.router, prefix="/api/v1", tags=["Telegram"])
app.include_router(diagnostic.router, prefix="/api/v1", tags=["Diagnostic"])

# Static files for Dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/dashboard", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(static_dir, "index.html"))
