"""
src/api/routers/diagnostic.py — LLM & Service Connection Diagnostic

Endpoint untuk mengecek apakah semua service tersambung dengan benar:
- LLM (SumoPod API)
- PostgreSQL
- Telegram Bot
"""
import time
import structlog
from fastapi import APIRouter
from pydantic import BaseModel

from src.config import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()


class ServiceStatus(BaseModel):
    status: str           # "ok" | "error" | "not_configured"
    message: str
    latency_ms: float | None = None
    detail: str | None = None


class DiagnosticResponse(BaseModel):
    llm: ServiceStatus
    database: ServiceStatus
    telegram: ServiceStatus
    overall: str          # "ok" | "degraded" | "error"


@router.get("/diagnostic", response_model=DiagnosticResponse)
async def run_diagnostic():
    """
    Cek koneksi ke semua service secara real-time.
    Gunakan ini untuk memverifikasi LLM_API_KEY, DATABASE_URL, dan TELEGRAM_BOT_TOKEN.
    """
    settings = get_settings()
    results = {}

    # -------------------------------------------------------------------------
    # 1. Cek LLM (SumoPod / OpenAI-compatible)
    # -------------------------------------------------------------------------
    t0 = time.monotonic()
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        llm = ChatOpenAI(
            model=settings.llm_model_name,
            openai_api_key=settings.llm_api_key,
            openai_api_base=settings.llm_base_url,
            max_tokens=20,
            timeout=15,
        )
        response = await llm.ainvoke([HumanMessage(content="Reply with: OK")])
        latency = round((time.monotonic() - t0) * 1000, 1)
        reply = response.content.strip()[:100]

        results["llm"] = ServiceStatus(
            status="ok",
            message=f"Tersambung ke {settings.llm_model_name} via SumoPod",
            latency_ms=latency,
            detail=f'Model reply: "{reply}"',
        )
        logger.info("diagnostic.llm_ok", latency_ms=latency, model=settings.llm_model_name)

    except Exception as e:
        latency = round((time.monotonic() - t0) * 1000, 1)
        err = str(e)

        # Beri pesan yang lebih actionable
        if "401" in err or "Unauthorized" in err:
            msg = "LLM_API_KEY tidak valid atau expired"
        elif "404" in err or "not found" in err.lower():
            msg = f"Model '{settings.llm_model_name}' tidak ditemukan di endpoint ini"
        elif "Connection" in err or "connect" in err.lower():
            msg = f"Tidak bisa terhubung ke {settings.llm_base_url}"
        elif not settings.llm_api_key or settings.llm_api_key == "your-sumopod-api-key-here":
            msg = "LLM_API_KEY belum diisi di .env"
        else:
            msg = "LLM error — lihat detail"

        results["llm"] = ServiceStatus(
            status="error",
            message=msg,
            latency_ms=latency,
            detail=err[:200],
        )
        logger.error("diagnostic.llm_error", error=err[:100])

    # -------------------------------------------------------------------------
    # 2. Cek PostgreSQL
    # -------------------------------------------------------------------------
    t0 = time.monotonic()
    try:
        import asyncpg
        # asyncpg butuh DSN biasa tanpa prefix "+asyncpg"
        dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(dsn=dsn, timeout=5)
        result = await conn.fetchval("SELECT version()")
        await conn.close()
        latency = round((time.monotonic() - t0) * 1000, 1)

        results["database"] = ServiceStatus(
            status="ok",
            message="PostgreSQL tersambung",
            latency_ms=latency,
            detail=result[:80] if result else None,
        )
    except Exception as e:
        latency = round((time.monotonic() - t0) * 1000, 1)
        results["database"] = ServiceStatus(
            status="error",
            message="PostgreSQL tidak bisa dihubungi",
            latency_ms=latency,
            detail=str(e)[:200],
        )

    # -------------------------------------------------------------------------
    # 3. Cek Telegram Bot
    # -------------------------------------------------------------------------
    t0 = time.monotonic()
    if not settings.telegram_bot_token or settings.telegram_bot_token == "your-telegram-bot-token-here":
        results["telegram"] = ServiceStatus(
            status="not_configured",
            message="TELEGRAM_BOT_TOKEN belum diisi di .env",
        )
    else:
        try:
            from telegram import Bot
            bot = Bot(token=settings.telegram_bot_token)
            me = await bot.get_me()
            latency = round((time.monotonic() - t0) * 1000, 1)
            results["telegram"] = ServiceStatus(
                status="ok",
                message=f"Bot @{me.username} aktif",
                latency_ms=latency,
                detail=f"Mode: {settings.telegram_mode} | Bot name: {me.full_name}",
            )
        except Exception as e:
            latency = round((time.monotonic() - t0) * 1000, 1)
            err = str(e)
            if "401" in err:
                msg = "TELEGRAM_BOT_TOKEN tidak valid"
            else:
                msg = "Telegram tidak bisa dihubungi"
            results["telegram"] = ServiceStatus(
                status="error",
                message=msg,
                latency_ms=latency,
                detail=err[:200],
            )

    # -------------------------------------------------------------------------
    # Overall status
    # -------------------------------------------------------------------------
    statuses = [results["llm"].status, results["database"].status, results["telegram"].status]
    if all(s == "ok" for s in statuses):
        overall = "ok"
    elif "error" in statuses and results["llm"].status == "error":
        overall = "error"
    else:
        overall = "degraded"

    return DiagnosticResponse(overall=overall, **results)
