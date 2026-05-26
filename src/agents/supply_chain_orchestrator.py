"""
src/agents/supply_chain_orchestrator.py — Agent D: Action Taker

Tugas:
- Eksekutor akhir yang menjalankan aksi nyata berdasarkan keputusan Negotiator
- Melakukan API Call ke sistem ERP, kurir, atau men-trigger Purchase Order
- Menyusun final response yang dikirim kembali ke pelanggan via Liaison
"""
import json
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import get_settings
from src.graph.state import GraphState, OrchestratorAction
from src.tools.erp_tools import update_erp_stock, trigger_purchase_order
from src.tools.courier_tools import dispatch_courier
from src.tools.vector_store import search_knowledge

logger = structlog.get_logger(__name__)

RESPONSE_COMPOSER_PROMPT = """Kamu adalah Senior Customer Relationship Manager Qhomemart.
Tugasmu adalah merangkai pesan akhir yang sangat profesional, empatis, dan SOLUTIF.

BATASAN DOMAIN:
- Kamu hanya berkomunikasi dalam konteks penyelesaian keluhan Qhomemart.
- Jangan menjawab atau merespons topik di luar keluhan pelanggan Qhomemart.

PANDUAN PENULISAN:
1. GREETING PERSONAL: Gunakan "Yth. Bapak/Ibu [Nama]" (ambil dari customer_profile). Jika pelanggan setia (is_loyal=true), tambahkan apresiasi atas loyalitasnya.
2. EMPATI TINGGI: Jika sentiment pelanggan negatif, gunakan bahasa yang lebih menenangkan. Contoh: "Kami sangat memahami kekecewaan Anda..."
3. STRUKTUR JELAS:
   - Jika keputusan adalah "multi_choice": Sajikan pilihan solusi dengan nomor (1, 2) agar pelanggan mudah memilih. Berikan rekomendasi mana yang terbaik bagi mereka (misal: Voucher 110% lebih untung).
   - Jika keputusan tunggal: Jelaskan langkah selanjutnya dan estimasi waktu secara spesifik (misal: 2x24 jam kerja).
4. CALL TO ACTION (CTA): 
   - Akhiri dengan instruksi yang jelas (misal: "Ketik angka 1 atau 2 untuk memilih solusi").
   - Berikan informasi bahwa tim kami siap membantu kapan saja.

DILARANG: Menggunakan bahasa kaku/robotic, memberikan janji palsu, atau menyalahkan pelanggan."""


def get_llm():
    settings = get_settings()
    return ChatOpenAI(
        model=settings.llm_model_name,
        openai_api_key=settings.llm_api_key,
        openai_api_base=settings.llm_base_url,
        temperature=0.4,  # Sedikit lebih kreatif untuk response yang natural
    )


async def supply_chain_orchestrator_node(state: GraphState) -> dict:
    """
    Node Supply Chain Orchestrator dalam LangGraph workflow.
    """
    session_id = state["session_id"]
    decision = state.get("compensation_decision")
    complaint = state.get("complaint")

    logger.info("orchestrator.start", session_id=session_id)
    from src.logger import broadcast_event
    broadcast_event("subagent_start", session_id, {"agent_id": "Supply Chain Orchestrator"})
    broadcast_event("reporting", session_id, {"agent_id": "Supply Chain Orchestrator", "message": "Mengeksekusi keputusan negosiasi (ERP, Kurir, PO)..."})

    if not decision or not complaint:
        return {"error": "Missing decision or complaint for orchestration"}

    actions_taken = []
    actions_failed = []
    erp_status = "not_triggered"
    courier_status = "not_triggered"
    po_triggered = False

    # --- Eksekusi aksi berdasarkan tipe keputusan ---
    if decision["decision_type"] == "replacement":
        # Update stok di ERP + dispatch kurir pengganti
        erp_result = await update_erp_stock(complaint["order_id"], action="reserve_replacement")
        if erp_result["success"]:
            actions_taken.append(f"Stok pengganti dipesan di ERP: {erp_result['message']}")
            erp_status = "updated"
        else:
            actions_failed.append(f"ERP update gagal: {erp_result['message']}")
            # Self-correction: Coba trigger PO jika stok habis
            po_result = await trigger_purchase_order(complaint["order_id"])
            if po_result["success"]:
                actions_taken.append(f"Purchase Order ke supplier di-trigger: {po_result['message']}")
                po_triggered = True
            else:
                actions_failed.append(f"PO gagal: {po_result['message']}")

        courier_result = await dispatch_courier(
            order_id=complaint["order_id"],
            action="pickup_and_deliver",
        )
        if courier_result["success"]:
            actions_taken.append(f"Kurir pengganti dijadwalkan: {courier_result['message']}")
            courier_status = "dispatched"
        else:
            actions_failed.append(f"Dispatch kurir gagal: {courier_result['message']}")

        # Jika ada kompensasi ekstra (voucher)
        if decision.get("compensation_value_idr", 0) > 0:
            actions_taken.append(
                f"Voucher kompensasi ekstra Rp {decision['compensation_value_idr']:,.0f} diterbitkan"
            )

    elif decision["decision_type"] == "voucher":
        actions_taken.append(
            f"Voucher diskon Rp {decision['compensation_value_idr']:,.0f} diterbitkan"
        )
        erp_status = "voucher_issued"

    elif decision["decision_type"] == "refund":
        erp_result = await update_erp_stock(complaint["order_id"], action="process_refund")
        if erp_result["success"]:
            actions_taken.append(f"Proses refund diinisiasi: {erp_result['message']}")
            erp_status = "refund_initiated"
        else:
            actions_failed.append(f"Refund gagal: {erp_result['message']}")

    elif decision["decision_type"] == "reject":
        actions_taken.append("Klaim ditolak — surat penjelasan disiapkan untuk pelanggan")

    elif decision["decision_type"] == "multi_choice":
        # No automated action — supervisor will approve and customer will pick a choice
        actions_taken.append("Pilihan kompensasi disiapkan untuk pelanggan (menunggu HITL approval)")

    orchestrator_action: OrchestratorAction = {
        "actions_taken": actions_taken,
        "actions_failed": actions_failed,
        "erp_update_status": erp_status,
        "courier_dispatch_status": courier_status,
        "po_triggered": po_triggered,
    }

    # --- Compose final response untuk pelanggan ---
    cp = state.get("customer_profile") or {}
    customer_name = cp.get("customer_name", "Pelanggan")
    order_id = complaint.get("order_id", "N/A")
    complaint_desc = complaint.get("complaint_description", "")

    # multi_choice: return clean structured response — skip LLM to avoid garbled "correction" text
    if decision["decision_type"] == "multi_choice":
        options_list = decision.get("options", [])
        letters = ["A", "B", "C", "D"]
        if options_list:
            opts_text = "\n".join(
                f"  *{letters[i]}.* {opt.get('label', opt.get('type', '?'))} — *Rp {opt.get('value', 0):,.0f}*"
                for i, opt in enumerate(options_list[:4])
            )
            final_response = (
                f"Yth. Bapak/Ibu {customer_name},\n\n"
                f"Kami sangat memahami kekecewaan Anda atas pesanan {order_id}. "
                f"Karena stok produk asli tidak tersedia dalam kondisi baik, "
                f"kami menawarkan pilihan kompensasi berikut:\n\n"
                f"📋 *Pilihan Anda:*\n{opts_text}\n\n"
                f"Silakan balas dengan *A*, *B*, atau *C* untuk memilih. "
                f"Tim kami siap membantu kapan saja."
            )
        else:
            final_response = (
                f"Yth. Bapak/Ibu {customer_name}, keluhan Anda sedang dalam proses persetujuan. "
                f"Tim kami akan menghubungi Anda segera. (Ref: {session_id})"
            )
        broadcast_event("subagent_stop", session_id, {
            "agent_id": "Supply Chain Orchestrator",
            "message": "Multi-choice disiapkan, menunggu HITL approval."
        })
        return {
            "orchestrator_action": orchestrator_action,
            "final_response": final_response,
        }

    response_context = f"""
Nama Pelanggan: {customer_name}
Order ID: {order_id}
Keluhan: {complaint_desc}
Keputusan: {decision['decision_type']}
Nilai kompensasi: Rp {decision['compensation_value_idr']:,.0f}
Aksi berhasil: {', '.join(actions_taken) if actions_taken else 'tidak ada'}
Aksi gagal: {', '.join(actions_failed) if actions_failed else 'tidak ada'}
Reasoning: {decision['reasoning']}
"""

    # RAG: ambil contoh respons dari kasus serupa untuk tone yang konsisten
    rag_query = f"{decision['decision_type']} {complaint.get('complaint_type', '')}"
    case_docs = await search_knowledge(rag_query, collection="resolved_cases", k=2)
    if case_docs:
        examples = "\n---\n".join(d.page_content for d in case_docs)
        response_context += f"\nREFERENSI POLA RESPONS KASUS SERUPA:\n{examples}\n"

    llm = get_llm()
    messages = [
        SystemMessage(content=RESPONSE_COMPOSER_PROMPT),
        HumanMessage(content=response_context),
    ]

    try:
        response = await llm.ainvoke(messages)
        final_response = response.content

        logger.info(
            "orchestrator.done",
            session_id=session_id,
            actions_taken=len(actions_taken),
            actions_failed=len(actions_failed),
        )

        broadcast_event("subagent_stop", session_id, {
            "agent_id": "Supply Chain Orchestrator",
            "message": f"Eksekusi Selesai. Aksi Berhasil: {len(actions_taken)}"
        })

        return {
            "orchestrator_action": orchestrator_action,
            "final_response": final_response,
            "messages": [response],
        }

    except Exception as e:
        logger.error("orchestrator.response_error", error=str(e))
        return {
            "orchestrator_action": orchestrator_action,
            "final_response": f"Keluhan Anda telah kami proses. Tim kami akan menghubungi Anda segera. (Ref: {session_id})",
        }


async def hitl_supervisor_node(state: GraphState) -> dict:
    """
    Node HITL — mengirim notifikasi email ke supervisor untuk approval manual.
    Dipanggil ketika kompensasi melebihi threshold.
    """
    import smtplib
    import asyncio
    from email.message import EmailMessage
    
    settings = get_settings()
    decision = state.get("compensation_decision")
    session_id = state["session_id"]
    audit = state.get("audit_result")
    profile = state.get("customer_profile")

    logger.info(
        "hitl.triggered",
        session_id=session_id,
        value=decision["compensation_value_idr"] if decision else 0,
    )
    
    from src.logger import broadcast_event
    broadcast_event("subagent_start", session_id, {"agent_id": "HITL Supervisor"})
    broadcast_event("reporting", session_id, {"agent_id": "HITL Supervisor", "message": "Mengirimkan email notifikasi ke manajer terkait..."})

    subject = f"[OmniResolve-AI] ⚠️ Tindakan Diperlukan: Approval Kompensasi (ID: {session_id[:8]})"
    
    # Pre-compute values
    d_type = decision['decision_type'] if decision else 'unknown'
    d_value = decision['compensation_value_idr'] if decision else 0
    d_reasoning = decision['reasoning'] if decision else '-'

    # Fallback plain text
    text_body = (
        f"APPROVAL REQUIRED — OmniResolve-AI\n\n"
        f"Session ID: {session_id}\n"
        f"Keputusan AI: {d_type}\n"
        f"Nilai Kompensasi: Rp {d_value:,.0f}\n\n"
        f"Alasan (Reasoning):\n{d_reasoning}\n\n"
        f"Silakan login ke dashboard untuk melakukan approval."
    )

    # Beautiful HTML Email
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background-color: #e63946; padding: 20px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; letter-spacing: 1px;">OMNIRESOLVE-AI</h1>
                <p style="color: #ffcdb2; margin: 5px 0 0 0; font-size: 14px;">Persetujuan Manajer Diperlukan</p>
            </div>
            
            <!-- Content -->
            <div style="padding: 30px;">
                <p style="color: #333333; font-size: 16px; line-height: 1.6;">
                    Halo Tim Manajemen,
                </p>
                <p style="color: #333333; font-size: 16px; line-height: 1.6;">
                    Sistem <strong>OmniResolve-AI</strong> telah menahan sebuah keputusan penyelesaian keluhan pelanggan karena nilai kompensasi melebihi batas persetujuan otomatis (Rp 1.000.000). Mohon tinjau rincian berikut:
                </p>
                
                <!-- Details Card -->
                <div style="background-color: #f8f9fa; border-left: 4px solid #457b9d; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; color: #6c757d; font-size: 14px; width: 40%;"><strong>Session ID</strong></td>
                            <td style="padding: 8px 0; color: #2b2d42; font-size: 14px; font-family: monospace;">{session_id}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6c757d; font-size: 14px;"><strong>Rekomendasi AI</strong></td>
                            <td style="padding: 8px 0; color: #2b2d42; font-size: 14px; text-transform: uppercase; font-weight: bold;">{d_type}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6c757d; font-size: 14px;"><strong>Total Nilai</strong></td>
                            <td style="padding: 8px 0; color: #e63946; font-size: 16px; font-weight: bold;">Rp {d_value:,.0f}</td>
                        </tr>
                    </table>
                </div>

                <!-- Reasoning Box -->
                <h3 style="color: #1d3557; font-size: 16px; margin-bottom: 10px;">Analisis & Chain of Thought AI:</h3>
                <div style="background-color: #edf2f4; padding: 15px; border-radius: 6px; color: #4a4e69; font-size: 14px; line-height: 1.6; font-style: italic;">
                    "{d_reasoning}"
                </div>

                <!-- Call to Action -->
                <div style="text-align: center; margin-top: 30px;">
                    <a href="{settings.base_url}/?hitl_session={session_id}" style="background-color: #2a9d8f; color: #ffffff; text-decoration: none; padding: 12px 25px; border-radius: 4px; font-weight: bold; font-size: 14px; display: inline-block;">
                        🚀 Tinjau & Ambil Keputusan di Dashboard
                    </a>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #f1faee; padding: 15px; text-align: center; font-size: 12px; color: #6c757d; border-top: 1px solid #dee2e6;">
                Pesan ini dibuat secara otomatis oleh OmniResolve-AI Agent Pipeline.<br>
                &copy; 2026 Qhomemart & OmniResolve
            </div>
        </div>
    </body>
    </html>
    """

    def send_email():
        if not settings.smtp_user or not settings.smtp_pass:
            raise ValueError("Kredensial SMTP belum dikonfigurasi di .env")
            
        msg = EmailMessage()
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype='html')
        
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        
        # Kirim ke 2 pimpinan yang di-request
        managers = ["haris.sandi23@students.utdi.ac.id", "agung.dwi23@students.utdi.ac.id"]
        msg["To"] = ", ".join(managers)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=3.0) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_pass)
            server.send_message(msg)

    try:
        await asyncio.to_thread(send_email)
        logger.info("hitl.email_notification_sent", session_id=session_id)
    except Exception as e:
        logger.warning("hitl.email_notification_failed", error=str(e))

    broadcast_event("subagent_stop", session_id, {
        "agent_id": "HITL Supervisor",
        "message": "Menunggu persetujuan manajer via Dashboard."
    })

    # Setelah notifikasi, tetap lanjut ke orchestrator (dengan flag sudah dinotif)
    return {
        "final_response": (
            "Keluhan Anda memerlukan persetujuan dari tim manajer kami karena nilainya melebihi limit otomatis. "
            "Kami telah mengirimkan notifikasi internal dan akan menghubungi Anda dalam waktu 1x24 jam. "
            f"Nomor referensi: {session_id}"
        )
    }
