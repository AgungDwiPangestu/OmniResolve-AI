"""
src/tools/inventory_tools.py — Inventory & Customer Profile Tools
Berkomunikasi langsung dengan database PostgreSQL.
"""
import random
import asyncpg
import structlog
from src.config import get_settings
from src.graph.state import CustomerProfile

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

async def check_inventory_status(order_id: str) -> dict:
    """
    Cek status stok untuk order tertentu dari database.
    """
    try:
        conn = await get_db_connection()
        query = """
            SELECT p.product_name, p.price_idr, p.stock_available, p.warehouse_condition
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE o.order_id = $1
            LIMIT 1
        """
        row = await conn.fetchrow(query, order_id)
        await conn.close()
        
        if row:
            return {
                "order_id": order_id,
                "product_name": row["product_name"],
                "price_idr": float(row["price_idr"]),
                "stock_available": row["stock_available"],
                "warehouse_condition": row["warehouse_condition"],
                "last_physical_check": "2026-05-10",
            }
    except Exception as e:
        logger.error("db.inventory_error", error=str(e))

    # Default untuk order yang tidak dikenal / error db
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
    Ambil profil pelanggan berdasarkan customer_id dari database.
    """
    try:
        conn = await get_db_connection()
        query = """
            SELECT customer_name, is_loyal, lifetime_value_idr, total_orders, previous_complaints
            FROM customers
            WHERE customer_id = $1
        """
        row = await conn.fetchrow(query, customer_id)
        await conn.close()
        
        if row:
            return {
                "customer_id": customer_id,
                "customer_name": row["customer_name"],
                "is_loyal": row["is_loyal"],
                "lifetime_value_idr": float(row["lifetime_value_idr"]),
                "total_orders": row["total_orders"],
                "previous_complaints": row["previous_complaints"],
            }
    except Exception as e:
        logger.error("db.customer_error", error=str(e))

    # Default untuk customer yang tidak dikenal
    return {
        "customer_id": customer_id,
        "customer_name": "Pelanggan",
        "is_loyal": False,
        "lifetime_value_idr": 0.0,
        "total_orders": 1,
        "previous_complaints": 0,
    }
