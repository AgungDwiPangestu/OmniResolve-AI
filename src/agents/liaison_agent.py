"""
src/agents/liaison_agent.py — Agent A: Front-End Intelligence

Tugas:
- Menjadi interface utama dengan pelanggan
- Melakukan sentiment analysis dan entity extraction
- Memastikan pelanggan merasa didengar sambil mengumpulkan data valid
"""
import json
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from src.config import get_settings
from src.graph.state import GraphState, ComplaintContext

logger = structlog.get_logger(__name__)

LIAISON_SYSTEM_PROMPT = """Kamu adalah Liaison Agent OmniResolve-AI (First Responder Qhomemart).
Tugas utamanya adalah menyerap emosi pelanggan dan memastikan mereka merasa didengar.

TUGASMU:
1. EMPATI EKSTREM: Jika pelanggan marah (sentiment < -0.5), mulailah dengan permintaan maaf yang sangat tulus.
2. CONVERSATIONAL GATHERING: Kamu berada dalam alur percakapan interaktif. Jika nomor order belum ada, tanyakan dengan ramah atau berikan petunjuk cara mencarinya.
3. DATA EXTRACTION: Ambil order_id, tipe keluhan, dan deskripsi jika ada di pesan.
4. DATA COMPLETE: Set `data_complete: true` HANYA jika kamu sudah mendapatkan nomor order (format ORD-...) DAN deskripsi keluhan. Jika belum lengkap, set `false`.
5. KONFIRMASI: Jika data sudah lengkap, beritahukan pelanggan bahwa keluhan mereka akan segera diproses secara otomatis.

OUTPUT FORMAT (JSON):
{
    "customer_response": "...",  
    "data_complete": true/false,  
    "complaint": {
        "customer_id": "...",
        "order_id": "...",
        "complaint_type": "damaged_item" | "missing_item" | "wrong_item" | "late_delivery" | "other",
        "complaint_description": "...",
        "sentiment_score": 0.0,
        "evidence_urls": []
    }
}

PENTING: Jadilah wajah Qhomemart yang ramah dan peduli."""


def get_llm():
    """Inisialisasi LLM dari SumoPod API (OpenAI-compatible)."""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.llm_model_name,
        openai_api_key=settings.llm_api_key,
        openai_api_base=settings.llm_base_url,
        temperature=0.3,
    )


async def liaison_agent_node(state: GraphState) -> dict:
    """
    Node Liaison Agent dalam LangGraph workflow.
    Dipanggil di awal workflow untuk memproses input pelanggan.
    """
    session_id = state["session_id"]
    logger.info("liaison_agent.start", session_id=session_id)
    from src.logger import broadcast_event
    broadcast_event("subagent_start", session_id, {"agent_id": "Liaison Agent"})
    broadcast_event("reporting", session_id, {"agent_id": "Liaison Agent", "message": "Berinteraksi dengan pelanggan, ekstrak entitas dan analisis sentimen..."})
    
    llm = get_llm()

    messages = [
        SystemMessage(content=LIAISON_SYSTEM_PROMPT),
        HumanMessage(content=state["raw_input"]),
    ]

    try:
        response = await llm.ainvoke(messages)
        
        raw_content = response.content.strip()
        
        # Robust JSON extraction from markdown
        import re
        json_match = re.search(r"({.*})", raw_content, re.DOTALL)
        if json_match:
            raw_content = json_match.group(1)
        
        try:
            result = json.loads(raw_content)
        except json.JSONDecodeError:
            # Try one more time by stripping markdown backticks if regex didn't catch it
            clean_content = raw_content.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean_content)

        complaint_data = result.get("complaint", {})
        complaint: ComplaintContext = {
            "customer_id": complaint_data.get("customer_id", "unknown"),
            "order_id": complaint_data.get("order_id", "unknown"),
            "complaint_type": complaint_data.get("complaint_type", "other"),
            "complaint_description": complaint_data.get("complaint_description", state["raw_input"]),
            "sentiment_score": float(complaint_data.get("sentiment_score", -0.5)),
            "evidence_urls": complaint_data.get("evidence_urls", []),
        }

        # Recovery: Jika order_id tidak ditemukan/unknown, coba cari manual pakai regex
        if complaint["order_id"] == "unknown":
            order_match = re.search(r"(ORD-[\w-]+)", state["raw_input"], re.IGNORECASE)
            if order_match:
                complaint["order_id"] = order_match.group(1).upper()

        logger.info(
            "liaison_agent.done",
            session_id=session_id,
            order_id=complaint["order_id"],
            complaint_type=complaint["complaint_type"],
            sentiment=complaint["sentiment_score"],
            data_complete=result.get("data_complete"),
        )
        
        broadcast_event("subagent_stop", session_id, {
            "agent_id": "Liaison Agent", 
            "message": f"Menemukan Order: {complaint['order_id']} | Tipe: {complaint['complaint_type']}"
        })

        return {
            "complaint": complaint,
            "messages": [response],
        }

    except (json.JSONDecodeError, KeyError) as e:
        logger.error("liaison_agent.parse_error", error=str(e))
        
        # Recovery manual jika JSON total gagal
        import re
        order_match = re.search(r"(ORD-[\w-]+)", state["raw_input"], re.IGNORECASE)
        recovered_order_id = order_match.group(1).upper() if order_match else "unknown"

        fallback_complaint: ComplaintContext = {
            "customer_id": "unknown",
            "order_id": recovered_order_id,
            "complaint_type": "other",
            "complaint_description": state["raw_input"],
            "sentiment_score": -0.5,
            "evidence_urls": [],
        }
        return {"complaint": fallback_complaint, "error": f"Liaison parse error: {e}"}
