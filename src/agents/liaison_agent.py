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

LIAISON_SYSTEM_PROMPT = """Kamu adalah Liaison Agent OmniResolve-AI — asisten layanan pelanggan yang SANGAT berempati dan profesional.

TUGASMU:
1. Menyambut pelanggan dengan hangat dan berempati
2. Melakukan sentiment analysis pada keluhan (nilai -1.0 hingga 1.0)
3. Mengekstrak informasi kunci dari keluhan:
   - customer_id (minta jika tidak ada)
   - order_id (minta jika tidak ada)
   - complaint_type: "damaged_item" | "missing_item" | "wrong_item" | "late_delivery" | "other"
   - complaint_description
   - evidence_urls (minta foto/video jika belum ada)
4. Jika semua data terkumpul, berikan konfirmasi kepada pelanggan bahwa keluhannya sedang diproses

OUTPUT FORMAT (JSON):
{
    "customer_response": "...",  // Response empati untuk pelanggan
    "data_complete": true/false,  // Apakah semua data sudah terkumpul
    "complaint": {
        "customer_id": "...",
        "order_id": "...",
        "complaint_type": "...",
        "complaint_description": "...",
        "sentiment_score": 0.0,
        "evidence_urls": []
    }
}

PENTING: Gunakan Bahasa Indonesia yang natural dan empatis. Jangan terkesan robotic."""


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
    logger.info("liaison_agent.start", session_id=state["session_id"])
    llm = get_llm()

    messages = [
        SystemMessage(content=LIAISON_SYSTEM_PROMPT),
        HumanMessage(content=state["raw_input"]),
    ]

    try:
        response = await llm.ainvoke(messages)
        result = json.loads(response.content)

        complaint_data = result.get("complaint", {})
        complaint: ComplaintContext = {
            "customer_id": complaint_data.get("customer_id", "unknown"),
            "order_id": complaint_data.get("order_id", "unknown"),
            "complaint_type": complaint_data.get("complaint_type", "other"),
            "complaint_description": complaint_data.get("complaint_description", state["raw_input"]),
            "sentiment_score": float(complaint_data.get("sentiment_score", -0.5)),
            "evidence_urls": complaint_data.get("evidence_urls", []),
        }

        logger.info(
            "liaison_agent.done",
            session_id=state["session_id"],
            complaint_type=complaint["complaint_type"],
            sentiment=complaint["sentiment_score"],
            data_complete=result.get("data_complete"),
        )

        return {
            "complaint": complaint,
            "messages": [response],
        }

    except (json.JSONDecodeError, KeyError) as e:
        logger.error("liaison_agent.parse_error", error=str(e))
        # Fallback — buat complaint dasar dari raw input
        fallback_complaint: ComplaintContext = {
            "customer_id": "unknown",
            "order_id": "unknown",
            "complaint_type": "other",
            "complaint_description": state["raw_input"],
            "sentiment_score": -0.5,
            "evidence_urls": [],
        }
        return {"complaint": fallback_complaint, "error": f"Liaison parse error: {e}"}
