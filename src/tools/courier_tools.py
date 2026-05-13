"""
src/tools/courier_tools.py — Mock Courier API Tools
Production: integrasi dengan JNE, J&T, SiCepat, atau Lalamove API.
"""
import asyncio


MOCK_COURIER_LOGS = {
    # Cat Tembok Eksterior - Terkirim aman, tapi komplain salah warna (dari sisi kurir aman)
    "ORD-QHM-003": {
        "tracking_id": "QHM-DEL-8821345",
        "status": "delivered",
        "last_update": "2026-05-12 16:45",
        "events": [
            {"time": "2026-05-12 08:00", "status": "Barang diambil dari Gudang Qhomemart Jogja", "location": "Yogyakarta"},
            {"time": "2026-05-12 10:30", "status": "Dalam perjalanan (Armada Internal)", "location": "Sleman"},
            {"time": "2026-05-12 16:45", "status": "Terkirim — diterima oleh: Bpk. Supri", "location": "Sleman"},
        ],
        "condition_on_pickup": "intact",
    },
    # Kloset Duduk - Terkirim tapi ada laporan retak dari kurir/kargo
    "ORD-QHM-004": {
        "tracking_id": "CARGO-5590234",
        "status": "delivered_with_damage_report",
        "last_update": "2026-05-11 14:20",
        "events": [
            {"time": "2026-05-09 09:00", "status": "Paket diambil dari Gudang Qhomemart", "location": "Yogyakarta"},
            {"time": "2026-05-10 20:15", "status": "Hub transit kargo — indikasi benturan ringan", "location": "Semarang"},
            {"time": "2026-05-11 14:20", "status": "Terkirim — ada laporan packing kayu sedikit rusak", "location": "Magelang"},
        ],
        "condition_on_pickup": "intact",
        "damage_reported_by_courier": True,
    },
    # Sofa - Terkirim pakai armada internal tapi basah/rusak di jalan
    "ORD-QHM-005": {
        "tracking_id": "QHM-DEL-9993331",
        "status": "delivered_with_damage_report",
        "last_update": "2026-05-13 10:00",
        "events": [
            {"time": "2026-05-13 08:00", "status": "Barang dimuat ke pickup Qhomemart", "location": "Yogyakarta"},
            {"time": "2026-05-13 09:30", "status": "Terkena hujan lebat di perjalanan, terpal bocor", "location": "Bantul"},
            {"time": "2026-05-13 10:00", "status": "Terkirim — catatan: basah/kotor", "location": "Bantul"},
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
