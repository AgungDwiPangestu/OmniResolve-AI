"""
src/telegram_bot/handlers.py — Telegram Message Handlers

Menangani semua jenis pesan masuk dari pelanggan:
- Text message → pengumpulan info / trigger pipeline
- Photo message → bukti kerusakan
- /start, /help, /status → command handlers
"""
import uuid
import structlog
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction

from src.telegram_bot.session import session_manager, ConversationStep
from src.graph.workflow import get_graph
from src.graph.state import GraphState

logger = structlog.get_logger(__name__)

# --- Pesan template ---
WELCOME_MSG = """👋 *Selamat datang di OmniResolve AI!*

Saya asisten layanan pelanggan otomatis yang siap membantu menyelesaikan masalah pesanan Anda dengan cepat.

Silakan ceritakan masalah yang Anda alami, misalnya:
• _"Barang saya datang dalam kondisi rusak"_
• _"Pesanan saya belum sampai sudah 2 minggu"_
• _"Barang yang diterima tidak sesuai pesanan"_

Ketik *nomor order* dan *deskripsi masalah* Anda untuk memulai 🚀"""

ASK_ORDER_ID_MSG = """📦 Terima kasih sudah menghubungi kami!

Untuk membantu Anda lebih cepat, mohon berikan *nomor order* Anda.
Format: `ORD-XXX` (tertera di email konfirmasi pembelian)"""

ASK_PHOTO_MSG = """📸 Apakah Anda memiliki foto atau video sebagai bukti?

Mengirimkan foto akan mempercepat proses verifikasi dan membantu kami memberikan solusi terbaik.

_(Kirim foto sekarang, atau ketik *skip* untuk melanjutkan tanpa foto)_"""

PROCESSING_MSG = """⏳ *Mohon tunggu sebentar...*

Tim agen kami sedang memproses keluhan Anda:
🔍 Liaison Agent → menganalisis keluhan
📊 Logistics Auditor → memverifikasi data
💼 Strategic Negotiator → menentukan solusi terbaik
⚡ Supply Chain → memproses tindakan

Estimasi waktu: 15-30 detik"""


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start."""
    chat_id = update.effective_chat.id
    session_manager.reset(chat_id)
    session = session_manager.get(chat_id)
    session.step = ConversationStep.GATHERING

    await update.message.reply_text(
        WELCOME_MSG,
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /help."""
    help_text = """🤖 *Cara menggunakan OmniResolve AI:*

1️⃣ Ceritakan masalah pesanan Anda
2️⃣ Berikan nomor order Anda (format: ORD-XXX)
3️⃣ Kirim foto bukti jika ada
4️⃣ Sistem akan memproses dan memberikan solusi

*Commands:*
/start — Mulai komplain baru
/status — Cek status komplain
/help — Tampilkan bantuan

*Jam operasional sistem:* 24/7 otomatis 🕐
*Untuk kasus darurat:* Sistem akan menghubungi supervisor kami"""

    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /status."""
    chat_id = update.effective_chat.id
    session = session_manager.get(chat_id)

    if session.step == ConversationStep.DONE:
        await update.message.reply_text(
            "✅ Komplain Anda telah selesai diproses. Ketik /start untuk komplain baru."
        )
    elif session.step == ConversationStep.PROCESSING:
        await update.message.reply_text("⏳ Komplain Anda sedang diproses...")
    else:
        await update.message.reply_text(
            "📝 Belum ada komplain aktif. Ketik /start untuk memulai."
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler utama untuk pesan teks dari pelanggan.
    Mengelola alur multi-turn conversation.
    """
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    session = session_manager.get(chat_id)

    logger.info("telegram.text_received", chat_id=chat_id, step=session.step, text_len=len(text))

    # --- Jika belum greeting, init dulu ---
    if session.step == ConversationStep.GREETING:
        session.step = ConversationStep.GATHERING
        await update.message.reply_text(WELCOME_MSG, parse_mode=ParseMode.MARKDOWN)
        return

    # --- Jika menunggu foto dan user skip ---
    if session.step == ConversationStep.WAITING_PHOTO and text.lower() == "skip":
        await _run_pipeline(update, context, session, chat_id)
        return

    # --- Jika pipeline sedang berjalan ---
    if session.step == ConversationStep.PROCESSING:
        await update.message.reply_text(
            "⏳ Mohon tunggu, sistem sedang memproses komplain Anda..."
        )
        return

    # --- Kumpulkan data ---
    if session.step == ConversationStep.GATHERING:
        # Coba ekstrak order ID dari teks (format ORD-XXX)
        import re
        order_match = re.search(r"(ORD-\w+)", text, re.IGNORECASE)
        if order_match and not session.order_id:
            session.order_id = order_match.group(1).upper()

        # Simpan pesan sebagai complaint text
        if not session.complaint_text:
            session.complaint_text = text
        else:
            session.complaint_text += f"\n{text}"

        # Jika order ID belum ada, minta
        if not session.order_id:
            await update.message.reply_text(ASK_ORDER_ID_MSG, parse_mode=ParseMode.MARKDOWN)
            return

        # Data sudah cukup → tanya foto
        session.step = ConversationStep.WAITING_PHOTO
        await update.message.reply_text(ASK_PHOTO_MSG, parse_mode=ParseMode.MARKDOWN)
        return


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk foto/gambar yang dikirim pelanggan sebagai bukti.
    """
    chat_id = update.effective_chat.id
    session = session_manager.get(chat_id)

    if session.step not in [ConversationStep.WAITING_PHOTO, ConversationStep.GATHERING]:
        await update.message.reply_text(
            "📸 Foto diterima! Ketik /start untuk memulai komplain baru dan lampirkan foto."
        )
        return

    # Ambil foto dengan resolusi terbaik
    photo = update.message.photo[-1]
    file_id = photo.file_id

    # Dapatkan URL file dari Telegram
    try:
        file = await context.bot.get_file(file_id)
        session.evidence_urls.append(file.file_path)
        logger.info("telegram.photo_received", chat_id=chat_id, file_path=file.file_path)
    except Exception as e:
        logger.warning("telegram.photo_error", error=str(e))
        # Simpan file_id sebagai fallback
        session.evidence_urls.append(f"tg://file/{file_id}")

    await update.message.reply_text(
        f"✅ Foto diterima! ({len(session.evidence_urls)} foto)\n\n"
        "Kirim foto lagi atau ketik *skip* untuk melanjutkan proses.",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Set step ke waiting_photo jika belum
    if session.step != ConversationStep.WAITING_PHOTO:
        session.step = ConversationStep.WAITING_PHOTO

    # Jika sudah ada complaint dan order_id, langsung proses
    if session.is_data_complete:
        await _run_pipeline(update, context, session, chat_id)


async def _run_pipeline(update, context, session, chat_id: int):
    """
    Internal: jalankan LangGraph pipeline dan kirim hasil ke pelanggan.
    """
    session.step = ConversationStep.PROCESSING

    # Tampilkan "sedang mengetik..." dan pesan processing
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    processing_msg = await update.message.reply_text(
        PROCESSING_MSG, parse_mode=ParseMode.MARKDOWN
    )

    session_id = f"tg-{chat_id}-{uuid.uuid4().hex[:8]}"
    pipeline_input = session.build_pipeline_input()

    logger.info("telegram.pipeline_start", chat_id=chat_id, session_id=session_id)

    try:
        initial_state: GraphState = {
            "messages": [],
            "raw_input": pipeline_input,
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

        graph = get_graph()
        final_state = await graph.ainvoke(initial_state)

        response_text = final_state.get("final_response") or (
            "Keluhan Anda telah kami terima dan sedang diproses. "
            "Tim kami akan segera menghubungi Anda."
        )
        decision = final_state.get("compensation_decision")

        # Hapus pesan "sedang diproses"
        await processing_msg.delete()

        # Kirim response utama
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ *Hasil Proses Keluhan*\n\n{response_text}",
            parse_mode=ParseMode.MARKDOWN,
        )

        # Kirim detail keputusan (untuk transparansi)
        if decision:
            detail_text = (
                f"📋 *Detail Keputusan:*\n"
                f"• Tipe: `{decision['decision_type']}`\n"
                f"• Nilai kompensasi: Rp {decision['compensation_value_idr']:,.0f}\n"
                f"• Ref: `{session_id}`"
            )
            if decision.get("requires_human_approval"):
                detail_text += "\n\n⚠️ _Kasus ini memerlukan persetujuan supervisor. Kami akan menghubungi Anda dalam 1x24 jam._"

            await context.bot.send_message(
                chat_id=chat_id,
                text=detail_text,
                parse_mode=ParseMode.MARKDOWN,
            )

        # Tombol untuk komplain baru
        keyboard = [[InlineKeyboardButton("🔄 Komplain Baru", callback_data="new_complaint")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=chat_id,
            text="Ada keluhan lain yang bisa kami bantu?",
            reply_markup=reply_markup,
        )

        session.step = ConversationStep.DONE
        logger.info("telegram.pipeline_done", chat_id=chat_id, session_id=session_id)

    except Exception as e:
        logger.error("telegram.pipeline_error", chat_id=chat_id, error=str(e))
        await processing_msg.delete()
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "😔 Maaf, sistem kami sedang mengalami gangguan sementara.\n"
                f"Keluhan Anda telah dicatat dengan referensi: `{session_id}`\n\n"
                "Tim kami akan segera menghubungi Anda."
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        session.step = ConversationStep.DONE


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk tombol inline keyboard."""
    query = update.callback_query
    await query.answer()

    if query.data == "new_complaint":
        chat_id = update.effective_chat.id
        session_manager.reset(chat_id)
        session = session_manager.get(chat_id)
        session.step = ConversationStep.GATHERING
        await query.message.reply_text(
            "📝 *Komplain Baru*\n\nSilakan ceritakan masalah Anda:",
            parse_mode=ParseMode.MARKDOWN,
        )
