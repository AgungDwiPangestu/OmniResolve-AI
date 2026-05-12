"""
src/graph/state.py — LangGraph State Definition

GraphState adalah "memori kerja" yang dibawa antar node (agent) di dalam graph.
Setiap agent membaca state dan mengembalikan update parsial.
"""
from typing import Annotated, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class ComplaintContext(TypedDict):
    """Data mentah dari pelanggan yang diekstrak oleh Liaison Agent."""
    customer_id: str
    order_id: str
    complaint_type: str          # misal: "damaged_item", "missing_item", "wrong_item"
    complaint_description: str
    sentiment_score: float       # -1.0 (sangat negatif) s/d 1.0 (positif)
    evidence_urls: list[str]     # URL foto/video bukti yang dikirim pelanggan


class AuditResult(TypedDict):
    """Hasil verifikasi dari Logistics & Inventory Auditor."""
    claim_valid: bool | None     # None = masih butuh data tambahan
    stock_status: str            # "available" | "depleted" | "damaged_in_warehouse"
    courier_log_summary: str
    cctv_metadata_summary: str
    audit_notes: str


class CustomerProfile(TypedDict):
    """Data profil pelanggan untuk CLV analysis."""
    customer_id: str
    customer_name: str
    is_loyal: bool               # Pelanggan setia berdasarkan histori
    lifetime_value_idr: float
    total_orders: int
    previous_complaints: int


class CompensationDecision(TypedDict):
    """Keputusan kompensasi dari Strategic Negotiator."""
    decision_type: str           # "voucher" | "replacement" | "refund" | "reject"
    compensation_value_idr: float
    reasoning: str               # Chain of Thought
    requires_human_approval: bool


class OrchestratorAction(TypedDict):
    """Aksi yang dieksekusi oleh Supply Chain Orchestrator."""
    actions_taken: list[str]     # List deskripsi aksi yang berhasil
    actions_failed: list[str]    # List aksi yang gagal + alasan
    erp_update_status: str
    courier_dispatch_status: str
    po_triggered: bool


class GraphState(TypedDict):
    """
    State utama LangGraph — dibawa sepanjang workflow.
    Setiap agent hanya mengisi field yang relevan dengan tugasnya.
    """
    # Conversation history (append-only, managed oleh LangGraph)
    messages: Annotated[list, add_messages]

    # Input awal dari pelanggan
    raw_input: str
    complaint: ComplaintContext | None

    # Hasil audit
    audit_result: AuditResult | None
    audit_retry_count: int        # Counter untuk self-correction loop

    # Profil pelanggan
    customer_profile: CustomerProfile | None

    # Keputusan
    compensation_decision: CompensationDecision | None

    # Aksi eksekusi
    orchestrator_action: OrchestratorAction | None

    # Final response ke pelanggan
    final_response: str | None

    # Metadata
    session_id: str
    error: str | None            # Jika ada error kritis
