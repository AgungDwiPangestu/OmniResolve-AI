"""
src/tools/courier_tools.py — Mock Courier API Tools
Production: integrasi dengan JNE, J&T, SiCepat, atau Lalamove API.
"""
import asyncio


MOCK_COURIER_LOGS = {
    "ORD-001": {
        "tracking_id": "JNE-8821345",
        "status": "delivered",
        "last_update": "2026-05-09 16:45",
        "events": [
            {"time": "2026-05-07 08:00", "status": "Paket diambil dari gudang", "location": "Jakarta Barat"},
            {"time": "2026-05-08 10:30", "status": "Dalam perjalanan", "location": "Tangerang"},
            {"time": "2026-05-09 16:45", "status": "Terkirim — diterima oleh: Budi H.", "location": "Jakarta Selatan"},
        ],
        "condition_on_pickup": "intact",
    },
    "ORD-004": {
        "tracking_id": "JNT-5590234",
        "status": "delivered_with_damage_report",
        "last_update": "2026-05-10 14:20",
        "events": [
            {"time": "2026-05-08 09:00", "status": "Paket diambil dari gudang", "location": "Bekasi"},
            {"time": "2026-05-09 20:15", "status": "Hub transit — paket dipindahkan", "location": "Karawang"},
            {"time": "2026-05-10 14:20", "status": "Terkirim — ada laporan kemasan rusak", "location": "Depok"},
        ],
        "condition_on_pickup": "intact",
        "damage_reported_by_courier": True,
    },
}


async def get_courier_log(order_id: str) -> dict:
    """
    Ambil log histori pengiriman untuk order tertentu.
    """
    # Simulasi network latency
    await asyncio.sleep(0.1)

    if order_id in MOCK_COURIER_LOGS:
        return MOCK_COURIER_LOGS[order_id]

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
