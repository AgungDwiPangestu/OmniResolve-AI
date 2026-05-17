"""
src/tools/courier_tools.py — Courier API Tools
Berkomunikasi dengan database logistik.
"""
import asyncio
import json
import asyncpg
import structlog
from src.config import get_settings

logger = structlog.get_logger(__name__)

async def get_db_connection():
    settings = get_settings()
    return await asyncpg.connect(
        user=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db
    )


async def get_courier_log(order_id: str) -> dict:
    """
    Ambil log histori pengiriman untuk order tertentu dari database.
    """
    try:
        conn = await get_db_connection()
        query = """
            SELECT tracking_id, status, condition_on_pickup, damage_reported_by_courier, delivery_logs
            FROM deliveries
            WHERE order_id = $1
        """
        row = await conn.fetchrow(query, order_id)
        await conn.close()
        
        if row:
            logs = row["delivery_logs"]
            events = json.loads(logs) if isinstance(logs, str) else logs
            last_update = events[-1]["time"] if events else "N/A"
            
            return {
                "tracking_id": row["tracking_id"],
                "status": row["status"],
                "last_update": last_update,
                "events": events,
                "condition_on_pickup": row["condition_on_pickup"],
                "damage_reported_by_courier": row["damage_reported_by_courier"],
            }
    except Exception as e:
        logger.error("db.courier_error", error=str(e))

    return {
        "tracking_id": f"UNKNOWN-{order_id}",
        "status": "no_data",
        "last_update": "N/A",
        "events": [],
        "condition_on_pickup": "unknown",
    }


async def dispatch_courier(order_id: str, action: str = "pickup_and_deliver") -> dict:
    """
    Pesan kurir baru untuk pickup/pengiriman pengganti.
    Action: "pickup_only" | "deliver_only" | "pickup_and_deliver"
    """
    await asyncio.sleep(0.1)  # Simulasi API call

    # Simulasi 90% success rate
    import random
    if random.random() < 0.9:
        return {
            "success": True,
            "tracking_id": f"NEW-{order_id}-{random.randint(10000, 99999)}",
            "message": f"Kurir dijadwalkan besok 09:00-12:00 untuk {action}",
            "estimated_pickup": "2026-05-13 09:00-12:00",
        }
    else:
        return {
            "success": False,
            "message": "Tidak ada kurir tersedia di area tersebut. Coba lagi besok.",
        }
