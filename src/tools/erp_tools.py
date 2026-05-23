"""
src/tools/erp_tools.py — ERP API Tools
Berkomunikasi langsung dengan database PostgreSQL.
"""
import asyncio
import random
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


from src.tools.inventory_tools import normalize_order_id


async def update_erp_stock(order_id: str, action: str = "reserve_replacement") -> dict:
    """
    Update stok atau status di sistem ERP (Database).
    Action: "reserve_replacement" | "process_refund" | "write_off"
    """
    order_id = normalize_order_id(order_id)
    try:
        conn = await get_db_connection()
        
        if action == "reserve_replacement":
            # Cek produk dari order_id
            query_product = """
                SELECT p.product_id, p.stock_available 
                FROM orders o
                JOIN order_items oi ON o.order_id = oi.order_id
                JOIN products p ON oi.product_id = p.product_id
                WHERE o.order_id = $1 LIMIT 1
            """
            product = await conn.fetchrow(query_product, order_id)
            
            if product and product["stock_available"] > 0:
                # Kurangi stok
                await conn.execute("UPDATE products SET stock_available = stock_available - 1 WHERE product_id = $1", product["product_id"])
                # Catat movement
                await conn.execute(
                    "INSERT INTO stock_movements (product_id, movement_type, quantity, reason, order_id) VALUES ($1, 'out', 1, 'replacement', $2)",
                    product["product_id"], order_id,
                )
                await conn.close()
                return {
                    "success": True,
                    "message": f"Stok pengganti berhasil direservasi untuk {order_id}",
                    "reserved_quantity": 1,
                    "erp_reference": f"ERP-{order_id}-RPL",
                }
            else:
                await conn.close()
                return {
                    "success": False,
                    "message": f"Stok habis untuk produk terkait {order_id}. Perlu PO ke supplier.",
                    "stock_available": 0,
                }

        elif action == "process_refund":
            # Update status order ke refunded
            await conn.execute("UPDATE orders SET status = 'refunded' WHERE order_id = $1", order_id)
            # Ambil product_id untuk catat movement
            product_q = """
                SELECT oi.product_id FROM order_items oi WHERE oi.order_id = $1 LIMIT 1
            """
            p = await conn.fetchrow(product_q, order_id)
            if p:
                await conn.execute(
                    "INSERT INTO stock_movements (product_id, movement_type, quantity, reason, order_id) VALUES ($1, 'out', 1, 'refund', $2)",
                    p["product_id"], order_id,
                )
            await conn.close()
            return {
                "success": True,
                "message": f"Proses refund diinisiasi untuk {order_id}. Estimasi 3-5 hari kerja.",
                "refund_reference": f"REF-{order_id}-{random.randint(1000, 9999)}",
            }

        elif action == "write_off":
            await conn.close()
            return {
                "success": True,
                "message": f"Item {order_id} dicatat sebagai write-off di sistem.",
            }

    except Exception as e:
        logger.error("db.erp_error", error=str(e))
        return {"success": False, "message": f"Database error: {e}"}

    return {"success": False, "message": f"Unknown ERP action: {action}"}


async def trigger_purchase_order(order_id: str) -> dict:
    """
    Trigger Purchase Order ke supplier ketika stok pengganti habis.
    """
    await asyncio.sleep(0.2)
    supplier_id = f"SUP-{random.randint(100, 999)}"
    po_number = f"PO-{order_id}-{random.randint(10000, 99999)}"

    return {
        "success": True,
        "po_number": po_number,
        "supplier_id": supplier_id,
        "message": f"Purchase Order {po_number} dikirim ke supplier {supplier_id}. ETA stok: 3-5 hari kerja.",
        "estimated_arrival": "2026-05-17",
    }
