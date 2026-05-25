"""
src/api/routers/admin_inventory.py — Admin Inventory & Dashboard API

GET /api/v1/admin/inventory/products   → daftar produk + stock info
GET /api/v1/admin/inventory/movements  → histori stock movements
GET /api/v1/admin/dashboard            → metrics Boss Room
"""
import structlog
from datetime import date, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.config import get_settings
from src.tools.inventory_tools import get_db_connection

logger = structlog.get_logger(__name__)
router = APIRouter()


# ─── Models ──────────────────────────────────────────────────────────────────

class ProductStock(BaseModel):
    product_id: str
    category: str | None
    product_name: str
    price_idr: float
    stock_available: int
    warehouse_location: str | None
    warehouse_condition: str


class StockMovement(BaseModel):
    id: int
    product_id: str
    product_name: str
    movement_type: str
    quantity: int
    reason: str | None
    order_id: str | None
    created_at: str


class DayCount(BaseModel):
    date: str
    count: int


class DecisionBreakdown(BaseModel):
    decision_type: str
    count: int
    total_compensation_idr: float


class DashboardMetrics(BaseModel):
    total_today: int
    resolved_today: int
    rejected_today: int
    pending_approval: int
    total_compensation_idr: float
    compensation_7days_idr: float
    money_saved_idr: float
    by_decision_type: list[DecisionBreakdown]
    last_7_days: list[DayCount]


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get(
    "/admin/inventory/products",
    response_model=list[ProductStock],
    summary="Daftar Produk & Stok",
    tags=["Inventory (Admin)"],
)
async def list_products():
    try:
        conn = await get_db_connection()
        rows = await conn.fetch(
            "SELECT product_id, category, product_name, price_idr, stock_available, warehouse_location, warehouse_condition FROM products ORDER BY category, product_name"
        )
        await conn.close()
        return [ProductStock(**dict(r)) for r in rows]
    except Exception as e:
        logger.error("admin.inventory.products_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/admin/inventory/movements",
    response_model=list[StockMovement],
    summary="Histori Stock Movements",
    tags=["Inventory (Admin)"],
)
async def list_movements(
    limit: int = Query(100, le=500),
    product_id: str | None = Query(None),
    movement_type: str | None = Query(None),
):
    try:
        conn = await get_db_connection()
        conditions = ["1=1"]
        params: list = []
        if product_id:
            params.append(product_id)
            conditions.append(f"sm.product_id = ${len(params)}")
        if movement_type:
            params.append(movement_type)
            conditions.append(f"sm.movement_type = ${len(params)}")
        params.append(limit)
        where = " AND ".join(conditions)
        query = f"""
            SELECT sm.id, sm.product_id, p.product_name, sm.movement_type,
                   sm.quantity, sm.reason, sm.order_id,
                   sm.created_at::text AS created_at
            FROM stock_movements sm
            JOIN products p ON sm.product_id = p.product_id
            WHERE {where}
            ORDER BY sm.created_at DESC
            LIMIT ${len(params)}
        """
        rows = await conn.fetch(query, *params)
        await conn.close()
        return [StockMovement(**dict(r)) for r in rows]
    except Exception as e:
        logger.error("admin.inventory.movements_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/admin/dashboard",
    response_model=DashboardMetrics,
    summary="Dashboard Metrics Boss Room",
    tags=["Inventory (Admin)"],
)
async def get_dashboard():
    try:
        conn = await get_db_connection()
        today = date.today()

        total_today = await conn.fetchval(
            "SELECT COUNT(*) FROM complaint_sessions WHERE created_at::date = $1", today
        ) or 0

        resolved_today = await conn.fetchval(
            "SELECT COUNT(*) FROM complaint_sessions WHERE status IN ('completed', 'approved') AND created_at::date = $1", today
        ) or 0

        rejected_today = await conn.fetchval(
            "SELECT COUNT(*) FROM complaint_sessions WHERE (decision_type = 'reject' OR status = 'rejected') AND created_at::date = $1", today
        ) or 0

        pending_approval = await conn.fetchval(
            "SELECT COUNT(*) FROM complaint_sessions WHERE status = 'pending_hitl'"
        ) or 0

        total_comp = await conn.fetchval(
            "SELECT COALESCE(SUM(compensation_value_idr), 0) FROM complaint_sessions WHERE decision_type != 'reject'"
        ) or 0.0

        comp_7d = await conn.fetchval(
            "SELECT COALESCE(SUM(compensation_value_idr), 0) FROM complaint_sessions WHERE decision_type != 'reject' AND created_at >= NOW() - INTERVAL '7 days'"
        ) or 0.0

        # Penghematan = biaya CS manual yang dihindari AI (Rp 2.5jt/komplain)
        # + nilai produk dari klaim fraud yang berhasil ditolak
        money_saved = await conn.fetchval(
            """
            SELECT
              (COUNT(*) * 2500000)
              + COALESCE((
                  SELECT SUM(COALESCE(p.price_idr, 0))
                  FROM complaint_sessions cs2
                  JOIN orders o ON cs2.order_id = o.order_id
                  JOIN order_items oi ON o.order_id = oi.order_id
                  JOIN products p ON oi.product_id = p.product_id
                  WHERE cs2.decision_type = 'reject'
              ), 0)
            FROM complaint_sessions
            """
        ) or 0.0

        breakdown_rows = await conn.fetch(
            "SELECT decision_type, COUNT(*) AS count, COALESCE(SUM(compensation_value_idr), 0) AS total_compensation_idr FROM complaint_sessions GROUP BY decision_type ORDER BY count DESC"
        )
        by_decision = [
            DecisionBreakdown(
                decision_type=r["decision_type"] or "unknown",
                count=r["count"],
                total_compensation_idr=float(r["total_compensation_idr"]),
            )
            for r in breakdown_rows
        ]

        daily_rows = await conn.fetch(
            """
            SELECT created_at::date AS date, COUNT(*) AS count
            FROM complaint_sessions
            WHERE created_at >= NOW() - INTERVAL '6 days'
            GROUP BY created_at::date
            ORDER BY date ASC
            """
        )
        last_7_days = [DayCount(date=str(r["date"]), count=r["count"]) for r in daily_rows]

        await conn.close()
        return DashboardMetrics(
            total_today=int(total_today),
            resolved_today=int(resolved_today),
            rejected_today=int(rejected_today),
            pending_approval=int(pending_approval),
            total_compensation_idr=float(total_comp),
            compensation_7days_idr=float(comp_7d),
            money_saved_idr=float(money_saved),
            by_decision_type=by_decision,
            last_7_days=last_7_days,
        )
    except Exception as e:
        logger.error("admin.dashboard_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
