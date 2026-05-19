import os
import logging
import logging.handlers
import sys
import asyncio
import httpx
from pathlib import Path
import structlog

# Dynamic Visualizer URL detection:
# When running inside the container (bridge network), use visualizer:8002
# When running outside (host dev mode), use localhost:8001 mapping
import threading

IS_CONTAINER = os.path.exists("/.dockerenv") or os.environ.get("POSTGRES_HOST") == "postgres"
DEFAULT_VISUALIZER = "http://visualizer:8002/api/v1/events" if IS_CONTAINER else "http://localhost:8001/api/v1/events"

VISUALIZER_URL = os.environ.get("VISUALIZER_URL", DEFAULT_VISUALIZER)

def _send_event_sync(payload: dict):
    try:
        with httpx.Client(timeout=2.0) as client:
            client.post(VISUALIZER_URL, json=payload)
    except Exception:
        # Ignore network errors silently for fire-and-forget robustness
        pass

def broadcast_event(event_type: str, session_id: str, data: dict = None):
    """
    Kirim event ke claude-office visualizer secara fire-and-forget (asynchronous).
    Ini memungkinkan animasi karakter di UI tanpa memperlambat sistem utama.
    """
    if data is None:
        data = {}
        
    payload = {
        "event_type": event_type,
        "session_id": session_id,
        "data": data
    }
    
    # Run in a background thread to prevent blocking the main process
    threading.Thread(target=_send_event_sync, args=(payload,), daemon=True).start()



def setup_logging(log_file_path: str = "logs/system.log"):
    """
    Konfigurasi sentral untuk mencatat SEMUA aktivitas sistem.
    Menggabungkan standard logging (yang dipakai library seperti Telegram) 
    ke dalam structlog agar formatnya seragam.
    """
    # 1. Pastikan direktori logs ada
    Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 2. Prosesor dasar yang akan diaplikasikan ke semua log
    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # 3. Konfigurasi structlog agar bertindak sebagai wrapper untuk standard logging
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 4. Buat Formatter untuk JSON (Disimpan ke file agar mudah di-parse system/database)
    file_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    
    # 5. Buat Formatter untuk Console (Format warna-warni cantik ala claude-office)
    console_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(colors=True),
        ],
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    
    # 6. Bajak Root Logger Python! (Ini yang menangkap log dari Telegram dll)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Opsional: Matikan log spam dari httpx jika terlalu berisik
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

