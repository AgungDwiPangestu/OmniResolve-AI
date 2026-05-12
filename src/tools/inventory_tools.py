"""
src/tools/inventory_tools.py — Mock Inventory & Customer Profile Tools

Di production, fungsi-fungsi ini akan memanggil API ERP nyata.
Untuk demo/kompetisi, data di-mock dengan data realistis.
"""
import random
from src.graph.state import CustomerProfile


# ---------------------------------------------------------------------------
# Mock data store
# ---------------------------------------------------------------------------
MOCK_INVENTORY = {
    "ORD-001": {"product_name": "Lemari Kayu 3 Pintu", "price_idr": 2_500_000, "stock": 3, "condition": "good"},
    "ORD-002": {"product_name": "Meja Makan 4 Kursi", "price_idr": 1_800_000, "stock": 0, "condition": "depleted"},
    "ORD-003": {"product_name": "Rak Dinding 5 Layer", "price_idr": 350_000, "stock": 15, "condition": "good"},
    "ORD-004": {"product_name": "Sofa 3 Seater", "price_idr": 4_200_000, "stock": 1, "condition": "damaged_in_warehouse"},
}

MOCK_CUSTOMERS = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "customer_name": "Budi Hartono",
        "is_loyal": True,
        "lifetime_value_idr": 15_000_000.0,
        "total_orders": 23,
        "previous_complaints": 1,
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "customer_name": "Sari Dewi",
        "is_loyal": False,
        "lifetime_value_idr": 250_000.0,
        "total_orders": 2,
        "previous_complaints": 0,
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
