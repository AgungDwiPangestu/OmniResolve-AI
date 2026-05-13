"""
src/tools/inventory_tools.py — Mock Inventory & Customer Profile Tools

Di production, fungsi-fungsi ini akan memanggil API ERP nyata.
Untuk demo/kompetisi, data di-mock dengan data realistis.
"""
import random
from src.graph.state import CustomerProfile


# ---------------------------------------------------------------------------
# Mock data store - QHOMEMART SCENARIOS
# ---------------------------------------------------------------------------
MOCK_INVENTORY = {
    # 1. Normal order - Granit Lantai
    "ORD-QHM-001": {"product_name": "Granit Lantai Niro Granite 60x60 (Dus)", "price_idr": 250_000, "stock": 50, "condition": "good"},
    
    # 2. Out of stock - Semen Instan
    "ORD-QHM-002": {"product_name": "Semen Instan Mortar Utama (MU-380) 40kg", "price_idr": 85_000, "stock": 0, "condition": "depleted"},
    
    # 3. Skenario Salah Barang / Salah Warna - Cat Tembok Eksterior
    "ORD-QHM-003": {"product_name": "Cat Tembok Dulux Weathershield 20L (Brilliant White)", "price_idr": 1_850_000, "stock": 12, "condition": "good"},
    
    # 4. Skenario Pecah/Retak saat pengiriman - Sanitary Kloset Duduk
    "ORD-QHM-004": {"product_name": "Kloset Duduk Toto Eco Washer Tipe CW421J", "price_idr": 2_400_000, "stock": 5, "condition": "damaged_in_warehouse"},

    # 5. Skenario Rusak Parah (Barang Mahal) - Hit threshold Human-in-the-Loop (> Rp 1jt)
    "ORD-QHM-005": {"product_name": "Sofa Minimalis L-Shape Fabric (Abu-abu)", "price_idr": 5_500_000, "stock": 2, "condition": "damaged_in_warehouse"},
}

MOCK_CUSTOMERS = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "customer_name": "Budi Hartono",
        "is_loyal": True,
        "lifetime_value_idr": 25_000_000.0,  # Sering belanja bahan bangunan/renovasi
        "total_orders": 12,
        "previous_complaints": 1,
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "customer_name": "Sari Dewi",
        "is_loyal": False,
        "lifetime_value_idr": 1_850_000.0,
        "total_orders": 2,
        "previous_complaints": 0,
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "customer_name": "Kontraktor Jaya Abadi",
        "is_loyal": True,
        "lifetime_value_idr": 150_000_000.0, # Akun B2B / Kontraktor
        "total_orders": 45,
        "previous_complaints": 2,
    },
    "CUST-999": {
        "customer_id": "CUST-999",
        "customer_name": "Pelanggan Baru",
        "is_loyal": False,
        "lifetime_value_idr": 0.0,
        "total_orders": 1,
        "previous_complaints": 0,
    },
}


async def check_inventory_status(order_id: str) -> dict:
    """
    Cek status stok untuk order tertentu.
    Production: panggil ERP API / database internal.
    """
    if order_id in MOCK_INVENTORY:
        item = MOCK_INVENTORY[order_id]
        return {
            "order_id": order_id,
            "product_name": item["product_name"],
            "price_idr": item["price_idr"],
            "stock_available": item["stock"],
            "warehouse_condition": item["condition"],
            "last_physical_check": "2026-05-10",
        }

    # Default untuk order yang tidak dikenal
    return {
        "order_id": order_id,
        "product_name": "Produk Tidak Dikenal",
        "price_idr": 500_000,
        "stock_available": random.randint(0, 5),
        "warehouse_condition": "unknown",
        "last_physical_check": "N/A",
    }


async def get_customer_profile_mock(customer_id: str) -> CustomerProfile:
    """
    Ambil profil pelanggan berdasarkan customer_id.
    Production: query ke database CRM.
    """
    if customer_id in MOCK_CUSTOMERS:
        return MOCK_CUSTOMERS[customer_id]  # type: ignore

    # Default untuk customer yang tidak dikenal
    return {
        "customer_id": customer_id,
        "customer_name": "Pelanggan",
        "is_loyal": False,
        "lifetime_value_idr": 0.0,
        "total_orders": 1,
        "previous_complaints": 0,
    }
