"""
src/api/routers/chat.py — OpenAI-Compatible Chat Endpoint

Endpoint ini mengikuti format OpenAI Chat Completion API
sehingga claude-office dan frontend lain bisa langsung terkoneksi
tanpa perlu konfigurasi khusus.

Cukup arahkan Base URL ke: http://localhost:8000/api/v1
"""
import uuid
import time
import structlog
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal

from src.graph.workflow import get_graph
from src.graph.state import GraphState

logger = structlog.get_logger(__name__)
router = APIRouter()


# --- OpenAI-compatible request/response models ---
class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "omni-resolve-ai"
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = None


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat endpoint.

    Cara koneksi dari claude-office:
    1. Base URL: http://localhost:8000/api/v1 (atau URL SumoPod deployment)
    2. API Key: isi dengan nilai apapun (endpoint ini tidak butuh auth untuk dev)
    3. Model: "omni-resolve-ai"

    Endpoint ini otomatis mengekstrak pesan terakhir dari user
    dan menjalankan seluruh pipeline multi-agent.
    """
    session_id = str(uuid.uuid4())
    
    from src.logger import broadcast_event
    broadcast_event("session_start", session_id, {"project_name": "OmniResolve-AI"})

    # Ambil pesan terakhir dari user
    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        last_user_message = "Halo, saya butuh bantuan."
    else:
        last_user_message = user_messages[-1].content

    logger.info("chat.request", session_id=session_id, message=last_user_message[:100])

    initial_state: GraphState = {
        "messages": [],
        "raw_input": last_user_message,
        "complaint": None,
        "audit_result": None,
        "audit_retry_count": 0,
        "customer_profile": None,
        "compensation_decision": None,
        "orchestrator_action": None,
        "final_response": None,
        "session_id": session_id,
        "error": None,
    }

    try:
        graph = get_graph()
        final_state = await graph.ainvoke(initial_state)
        response_text = final_state.get("final_response") or "Keluhan Anda sedang diproses oleh tim kami."

        # Tambahkan Chain of Thought ke response jika ada
        decision = final_state.get("compensation_decision")
        if decision and decision.get("reasoning"):
            response_text += f"\n\n---\n**Chain of Thought (Audit Trail):**\n{decision['reasoning']}"

    except Exception as e:
        logger.error("chat.pipeline_error", session_id=session_id, error=str(e))
        response_text = "Maaf, sistem sedang mengalami gangguan. Silakan coba lagi."
        from src.logger import broadcast_event
        broadcast_event("session_end", session_id, {"project_name": "OmniResolve-AI", "error": str(e)})

    from src.logger import broadcast_event
    broadcast_event("session_end", session_id, {"project_name": "OmniResolve-AI", "response": response_text})

    return ChatCompletionResponse(
        id=f"chatcmpl-{session_id}",
        created=int(time.time()),
        model=request.model,
        choices=[
            ChatChoice(
                index=0,
                message=ChatMessage(role="assistant", content=response_text),
                finish_reason="stop",
            )
        ],
    )
