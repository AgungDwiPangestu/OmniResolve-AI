"""
src/tools/erp_tools.py — Mock ERP API Tools
Production: integrasi dengan SAP, Odoo, atau sistem ERP internal.
"""
import asyncio
import random


async def update_erp_stock(order_id: str, action: str = "reserve_replacement") -> dict:
    """
    Update stok di sistem ERP.
    Action: "reserve_replacement" | "process_refund" | "write_off"
    """
    await asyncio.sleep(0.15)  # Simulasi API latency ERP

    if action == "reserve_replacement":
        if random.random() < 0.8:  # 80% stok tersedia
            return {
                "success": True,
                "message": f"Stok pengganti berhasil direservasi untuk {order_id}",
                "reserved_quantity": 1,
                "erp_reference": f"ERP-{order_id}-RPL",
            }
        else:
            return {
                "success": False,
                "message": f"Stok habis untuk produk terkait {order_id}. Perlu PO ke supplier.",
                "stock_available": 0,
            }

    elif action == "process_refund":
        return {
            "success": True,
            "message": f"Proses refund diinisiasi untuk {order_id}. Estimasi 3-5 hari kerja.",
            "refund_reference": f"REF-{order_id}-{random.randint(1000, 9999)}",
        }

    elif action == "write_off":
        return {
            "success": True,
            "message": f"Item {order_id} dicatat sebagai write-off di sistem.",
        }

    return {"success": False, "message": f"Unknown ERP action: {action}"}


async def trigger_purchase_order(order_id: str) -> dict:
    """
    Trigger Purchase Order ke supplier ketika stok pengganti habis.
    Self-correction: dipanggil otomatis oleh Orchestrator saat ERP stok kosong.
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
