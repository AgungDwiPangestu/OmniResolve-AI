"""
src/telegram_bot/session.py — Session Manager

Menyimpan state percakapan per pelanggan berdasarkan chat_id Telegram.
Memungkinkan Liaison Agent meminta data tambahan (foto, order ID, dsb.)
dalam multi-turn conversation sebelum pipeline dijalankan.
"""
from dataclasses import dataclass, field
from enum import Enum


class ConversationStep(str, Enum):
    """Tahap dalam alur percakapan dengan pelanggan."""
    GREETING         = "greeting"          # Baru mulai
    GATHERING        = "gathering"         # Mengumpulkan info (order ID, deskripsi)
    WAITING_PHOTO    = "waiting_photo"     # Menunggu foto bukti
    PROCESSING       = "processing"        # Pipeline agent sedang berjalan
    AWAITING_CHOICE  = "awaiting_choice"   # Menunggu pilihan pelanggan (ketik 1 atau 2)
    DONE             = "done"              # Selesai, siap terima komplain baru
    ESCALATED        = "escalated"         # Menunggu respon CS Manusia
    CHECKING_STATUS  = "checking_status"   # Menunggu input kode referensi atau tombol lacak


@dataclass
class CustomerSession:
    """State percakapan satu pelanggan."""
    chat_id: int
    step: ConversationStep = ConversationStep.GREETING

    # Data yang dikumpulkan secara bertahap
    customer_name: str = ""
    complaint_text: str = ""
    order_id: str = ""
    evidence_urls: list[str] = field(default_factory=list)

    # Data untuk AWAITING_CHOICE (setelah pipeline selesai)
    last_session_id: str = ""
    last_decision_type: str = ""

    # Untuk membangun input ke pipeline
    @property
    def is_data_complete(self) -> bool:
        """Apakah data minimum sudah terkumpul untuk menjalankan pipeline?"""
        return bool(self.complaint_text and self.order_id)

    def build_pipeline_input(self) -> str:
        """Bangun string input untuk LangGraph pipeline."""
        parts = [self.complaint_text]
        if self.order_id:
            parts.append(f"Order ID: {self.order_id}")
        if self.customer_name:
            parts.append(f"Nama pelanggan: {self.customer_name}")
        if self.evidence_urls:
            parts.append(f"Foto bukti: {', '.join(self.evidence_urls)}")
        return "\n".join(parts)

    def reset(self):
        """Reset sesi untuk komplain baru."""
        self.step = ConversationStep.GREETING
        self.complaint_text = ""
        self.order_id = ""
        self.evidence_urls = []
        self.last_session_id = ""
        self.last_decision_type = ""


class SessionManager:
    """
    In-memory session manager.
    Production: ganti dengan Redis atau PostgreSQL untuk persistensi.
    """
    def __init__(self):
        self._sessions: dict[int, CustomerSession] = {}

    def get(self, chat_id: int) -> CustomerSession:
        """Ambil atau buat sesi baru untuk chat_id."""
        if chat_id not in self._sessions:
            self._sessions[chat_id] = CustomerSession(chat_id=chat_id)
        return self._sessions[chat_id]

    def reset(self, chat_id: int):
        """Reset sesi pelanggan (untuk komplain baru)."""
        if chat_id in self._sessions:
            self._sessions[chat_id].reset()


# Singleton
session_manager = SessionManager()
