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

from src.config import get_settings
from src.telegram_bot.session import session_manager, ConversationStep
from src.graph.workflow import get_graph
from src.graph.state import GraphState

logger = structlog.get_logger(__name__)

import os
import json
import asyncpg
from datetime import datetime

GROUP_CHATS_FILE = os.path.join(os.path.dirname(__file__), "group_chats.json")

def load_group_chats() -> dict:
    if os.path.exists(GROUP_CHATS_FILE):
        try:
            with open(GROUP_CHATS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"warehouse_chat_id": None, "courier_chat_id": None}

def save_group_chats(data: dict):
    try:
        with open(GROUP_CHATS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error("telegram.save_group_chats_error", error=str(e))


async def send_to_warehouse_group(context, session_id: str, order_id: str):
    """Mengirim instruksi pengambilan barang ke grup Gudang yang terdaftar."""
    data = load_group_chats()
    warehouse_chat_id = data.get("warehouse_chat_id")
    
    if not warehouse_chat_id:
        logger.warning("telegram.warehouse_group_not_registered", session_id=session_id)
        return
        
    settings = get_settings()
    try:
        conn = await asyncpg.connect(
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db
        )
        
        # Ambil produk dan detail pelanggan berdasarkan order_id
        query = """
            SELECT c.customer_name, c.phone, c.address, p.product_name, oi.quantity
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE o.order_id = $1
        """
        rows = await conn.fetch(query, order_id)
        await conn.close()
        
        if not rows:
            logger.warning("telegram.warehouse_order_not_found", order_id=order_id)
            return
            
        customer_name = rows[0]["customer_name"]
        phone = rows[0]["phone"]
        address = rows[0]["address"]
        
        # Format daftar produk
        items_list = ""
        for row in rows:
            items_list += f"• 📦 *{row['product_name']}* - {row['quantity']} unit\n"
            
        msg = (
            f"📦 *PERINTAH PENGAMBILAN BARANG GUDANG*\n\n"
            f"Ditemukan laporan kerusakan valid untuk pelanggan:\n"
            f"• *Nama Pelanggan:* {customer_name} ({phone})\n"
            f"• *Alamat Pengiriman:* {address}\n"
            f"• *Nomor Order:* `{order_id}`\n"
            f"• *Ref Sesi:* `{session_id}`\n\n"
            f"📋 *Daftar Barang yang Harus Disiapkan:*\n"
            f"{items_list}\n"
            f"💡 _Silakan gudang siapkan barang tersebut. Begitu barang siap diserahkan ke kurir, silakan klik tombol di bawah ini._"
        )
        
        keyboard = [[InlineKeyboardButton("✅ Selesai (Siap Dikirim)", callback_data=f"wh_done:{session_id}:{order_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=warehouse_chat_id,
            text=msg,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info("telegram.sent_to_warehouse", session_id=session_id, order_id=order_id)
        
    except Exception as e:
        logger.error("telegram.send_to_warehouse_error", error=str(e))

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


async def query_and_send_status(chat_id: int, ref_code: str | None, update_or_query) -> bool:
    """Helper untuk mengambil status dari database PostgreSQL dan mengirimkannya ke Telegram."""
    settings = get_settings()
    import asyncpg
    
    # Deteksi apakah dipanggil dari tombol (callback_query) atau pesan teks biasa
    is_callback = hasattr(update_or_query, "message") and not hasattr(update_or_query, "reply_text")
    msg_target = update_or_query.message if is_callback else update_or_query
    
    try:
        conn = await asyncpg.connect(
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db
        )
        
        if ref_code:
            # Cari berdasarkan ID sesi spesifik
            row = await conn.fetchrow(
                "SELECT session_id, status, decision_type, compensation_value_idr, final_response, created_at FROM complaint_sessions WHERE session_id = $1",
                ref_code
            )
        else:
            # Lacak laporan terakhir untuk chat_id ini
            row = await conn.fetchrow(
                "SELECT session_id, status, decision_type, compensation_value_idr, final_response, created_at FROM complaint_sessions WHERE session_id LIKE $1 ORDER BY created_at DESC LIMIT 1",
                f"tg-{chat_id}-%"
            )
            
        await conn.close()
        
        if row:
            session_id = row["session_id"]
            status = row["status"]
            decision_type = row["decision_type"]
            comp_value = row["compensation_value_idr"] or 0
            final_response = row["final_response"]
            
            # Map status
            status_map = {
                "completed": "✅ SELESAI (Resolved)",
                "pending_hitl": "⏳ MENUNGGU PERSETUJUAN SUPERVISOR (Pending HITL Approval)",
                "escalated": "👨‍💼 DIALIHKAN KE CS MANUSIA (Escalated to CS)",
                "rejected": "❌ KLAIM DITOLAK (Rejected)"
            }
            status_label = status_map.get(status, status.upper())
            
            type_emoji = {
                "replacement": "🔄 Ganti Baru (Replacement)",
                "refund": "💰 Pengembalian Dana (Refund)",
                "voucher": "🎫 Voucher Kompensasi",
                "reject": "❌ Klaim Ditolak",
            }
            decision_label = type_emoji.get(decision_type, decision_type or "Sedang diproses")
            
            msg = (
                f"📋 *Laporan Komplain: `{session_id}`*\n\n"
                f"• *Status:* {status_label}\n"
                f"• *Keputusan:* {decision_label}\n"
            )
            if comp_value > 0:
                msg += f"• *Nilai Kompensasi:* Rp {comp_value:,.0f}\n"
                
            if final_response:
                msg += f"\n💬 *Tindak Lanjut Perusahaan:*\n_{final_response}_"
            else:
                msg += f"\n💬 *Tindak Lanjut:* Keluhan Anda telah tercatat dan sedang dalam penyelesaian operasional."
                
            if is_callback:
                await msg_target.edit_text(msg, parse_mode=ParseMode.MARKDOWN)
            else:
                await msg_target.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            return True
        else:
            msg = ""
            if ref_code:
                msg = (
                    f"❌ Referensi keluhan `{ref_code}` tidak ditemukan di sistem kami.\n\n"
                    "Silakan masukkan kembali kode referensi keluhan Anda secara tepat (misal: `tg-8289635135-xxxxxxxx`):"
                )
            else:
                msg = (
                    "📝 Belum ada komplain aktif yang tercatat untuk akun Anda.\n\n"
                    "Silakan ketik /start untuk memulai keluhan baru."
                )
            
            if is_callback:
                await msg_target.edit_text(msg, parse_mode=ParseMode.MARKDOWN)
            else:
                await msg_target.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            return False
            
    except Exception as e:
        logger.error("telegram.status_query_error", error=str(e))
        err_msg = "⚠️ Gagal menghubungkan ke server status. Silakan coba beberapa saat lagi."
        if is_callback:
            await msg_target.edit_text(err_msg)
        else:
            await msg_target.reply_text(err_msg)
        return False


async def cmd_register_warehouse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk mendaftarkan grup gudang (Warehouse)."""
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title or "Grup"
    
    # Pastikan ini dipanggil di grup/supergrup
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("⚠️ Perintah ini hanya dapat dijalankan di dalam grup Telegram.")
        return
        
    data = load_group_chats()
    data["warehouse_chat_id"] = chat_id
    save_group_chats(data)
    
    await update.message.reply_text(
        f"🚀 *Grup Gudang Berhasil Didaftarkan!*\n\n"
        f"• *Nama Grup:* `{chat_title}`\n"
        f"• *Chat ID:* `{chat_id}`\n\n"
        f"Semua pesanan penggantian barang (Replacement) di bawah Rp 1.000.000 akan otomatis dikirim ke grup ini untuk dipersiapkan.",
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_register_courier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk mendaftarkan grup kurir (Courier)."""
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title or "Grup"
    
    # Pastikan ini dipanggil di grup/supergrup
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("⚠️ Perintah ini hanya dapat dijalankan di dalam grup Telegram.")
        return
        
    data = load_group_chats()
    data["courier_chat_id"] = chat_id
    save_group_chats(data)
    
    await update.message.reply_text(
        f"🚚 *Grup Kurir Berhasil Didaftarkan!*\n\n"
        f"• *Nama Grup:* `{chat_title}`\n"
        f"• *Chat ID:* `{chat_id}`\n\n"
        f"Instruksi pengiriman barang yang sudah siap dari gudang akan otomatis dikirim ke grup ini.",
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /status."""
    chat_id = update.effective_chat.id
    session = session_manager.get(chat_id)
    
    # Ambil argumen jika ada (misal: /status tg-8289635135-525038dd)
    args = context.args
    ref_code = None
    if args:
        ref_code = args[0].strip()
        
    if ref_code:
        # Jika pengguna langsung mengirimkan ID referensi beserta command
        await query_and_send_status(chat_id, ref_code, update)
        session.step = ConversationStep.DONE
        return
        
    # Periksa apakah ada sesi pengisian keluhan aktif yang sedang berjalan
    if session.step == ConversationStep.PROCESSING:
        await update.message.reply_text("⏳ Komplain Anda saat ini sedang diproses oleh tim agen kami...")
        return
    elif session.step == ConversationStep.GATHERING:
        await update.message.reply_text("📝 Anda sedang berada dalam proses penginputan komplain. Silakan kirimkan keluhan Anda.")
        return

    # Pindahkan step ke checking_status untuk menangkap input teks berikutnya
    session.step = ConversationStep.CHECKING_STATUS
    
    keyboard = [
        [InlineKeyboardButton("🔍 Lacak Laporan Terakhir", callback_data="status_last")],
        [InlineKeyboardButton("❌ Batal", callback_data="status_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔍 *Lacak Status Komplain*\n\n"
        "Untuk melihat perkembangan laporan keluhan Anda, silakan lakukan salah satu langkah berikut:\n\n"
        "1️⃣ **Balas obrolan ini langsung** dengan mengetik kode referensi keluhan Anda (misal: `tg-8289635135-xxxxxxxx`)\n"
        "2️⃣ **Klik tombol di bawah ini** untuk melacak laporan paling terakhir yang Anda buat secara otomatis.",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /cancel."""
    chat_id = update.effective_chat.id
    session_manager.reset(chat_id)
    await update.message.reply_text(
        "🚫 Proses komplain dibatalkan. Ketik /start jika Anda ingin mengulang dari awal."
    )


async def cmd_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /faq."""
    keyboard = [
        [InlineKeyboardButton("Kebijakan Retur", callback_data="faq_return")],
        [InlineKeyboardButton("Jam Operasional", callback_data="faq_hours")],
        [InlineKeyboardButton("Lacak Pengiriman", callback_data="faq_tracking")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "❓ *Pusat Bantuan Otomatis*\nSilakan pilih topik yang ingin Anda ketahui:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_human(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /human."""
    chat_id = update.effective_chat.id
    session = session_manager.get(chat_id)
    session.step = ConversationStep.ESCALATED
    await update.message.reply_text(
        "👨‍💼 *Eskalasi ke Customer Service*\n\n"
        "AI kami telah berhenti memproses sesi Anda. Agen CS manusia kami akan segera bergabung dalam obrolan ini. Mohon tunggu beberapa saat...",
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler utama untuk pesan teks dari pelanggan.
    Mengelola alur multi-turn conversation.
    """
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_title = update.effective_chat.title or ""
    text = update.message.text.strip()
    session = session_manager.get(chat_id)

    logger.info("telegram.text_received", chat_id=chat_id, step=session.step, text_len=len(text))

    # --- Jika pesan dikirim di dalam Grup/Supergrup (Operasional Gudang/Kurir) ---
    if chat_type in ["group", "supergroup"]:
        # Auto-register group chats if the title matches and they aren't registered yet
        data = load_group_chats()
        updated = False
        title_lower = chat_title.lower()
        if "gudang" in title_lower or "warehouse" in title_lower:
            if data.get("warehouse_chat_id") != chat_id:
                data["warehouse_chat_id"] = chat_id
                updated = True
                logger.info("telegram.auto_register_warehouse", chat_id=chat_id, title=chat_title)
        elif "kurir" in title_lower or "courier" in title_lower:
            if data.get("courier_chat_id") != chat_id:
                data["courier_chat_id"] = chat_id
                updated = True
                logger.info("telegram.auto_register_courier", chat_id=chat_id, title=chat_title)
        
        if updated:
            save_group_chats(data)
            await update.message.reply_text(
                f"⚡ *[Auto-Register]* Grup ini otomatis terdaftar sebagai "
                f"{'Gudang Qhomemart' if 'gudang' in title_lower or 'warehouse' in title_lower else 'Kurir Qhomemart'}!"
            )
        return  # Jangan proses percakapan AI untuk pesan grup biasa

    # --- Jika sedang mengecek status komplain ---
    if session.step == ConversationStep.CHECKING_STATUS:
        ref_code = text.strip()
        success = await query_and_send_status(chat_id, ref_code, update)
        if success:
            session.step = ConversationStep.DONE
        return

    # --- Jika belum greeting, init dulu ---
    if session.step == ConversationStep.GREETING:
        session.step = ConversationStep.GATHERING
        await update.message.reply_text(WELCOME_MSG, parse_mode=ParseMode.MARKDOWN)
        return

    # --- Jika status ESCALATED ---
    if session.step == ConversationStep.ESCALATED:
        await update.message.reply_text(
            "⏳ Anda saat ini dalam antrean CS Manusia. AI kami dinonaktifkan sementara untuk sesi Anda."
        )
        return

    # --- Jika menunggu foto dan user skip ---
    if session.step == ConversationStep.WAITING_PHOTO and text.lower() == "skip":
        await _run_pipeline(update, context, session, chat_id)
        return

    # --- Jika menunggu pilihan resolusi (ketik 1 atau 2) ---
    if session.step == ConversationStep.AWAITING_CHOICE:
        choice = text.strip()
        ref = f"`{session.last_session_id}`" if session.last_session_id else ""
        if choice == "1":
            await update.message.reply_text(
                f"✅ *Voucher / Kompensasi Berhasil Diaktifkan!*\n\n"
                f"Voucher kompensasi telah kami aktifkan ke akun Qhomemart Anda.\n"
                f"• Referensi: {ref}\n\n"
                "Voucher dapat digunakan pada pembelian berikutnya. "
                "Terima kasih telah mempercayakan masalah Anda kepada kami 🙏",
                parse_mode=ParseMode.MARKDOWN,
            )
            session.step = ConversationStep.DONE
        elif choice == "2":
            await update.message.reply_text(
                f"📄 *Permintaan Surat Penjelasan Resmi Diterima*\n\n"
                f"Tim kami akan menyiapkan dokumen surat penjelasan resmi dan mengirimkannya ke email Anda dalam 1×24 jam kerja.\n"
                f"• Referensi: {ref}\n\n"
                "Apabila ada pertanyaan lebih lanjut, silakan hubungi CS kami. 🙏",
                parse_mode=ParseMode.MARKDOWN,
            )
            session.step = ConversationStep.DONE
        else:
            await update.message.reply_text(
                "⚠️ Pilihan tidak valid.\n\nKetik *1* untuk mengaktifkan kompensasi atau *2* untuk surat penjelasan resmi.",
                parse_mode=ParseMode.MARKDOWN,
            )
        return

    # --- Jika pipeline sedang berjalan ---
    if session.step == ConversationStep.PROCESSING:
        await update.message.reply_text(
            "⏳ Mohon tunggu, sistem sedang memproses komplain Anda..."
        )
        return

    # --- Kumpulkan data ---
    if session.step == ConversationStep.GATHERING:
        # Pindahkan kendali percakapan ke Liaison Agent (AI)
        await _run_liaison_only(update, context, session)
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


async def _run_liaison_only(update: Update, context: ContextTypes.DEFAULT_TYPE, session):
    """
    Menjalankan percakapan interaktif hanya dengan Liaison Agent.
    AI akan mengobrol sampai data (Order ID & Keluhan) terkumpul.
    """
    from src.agents.liaison_agent import liaison_agent_node
    from src.graph.state import GraphState
    
    chat_id = update.effective_chat.id
    text = update.message.text

    # Tampilkan status "typing..."
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # Siapkan state untuk Liaison
    state: GraphState = {
        "messages": [],
        "raw_input": text,
        "complaint": {
            "customer_id": "unknown",
            "order_id": session.order_id or "unknown",
            "complaint_type": "other",
            "complaint_description": session.complaint_text or "unknown",
            "sentiment_score": 0.0,
            "evidence_urls": session.evidence_urls,
        },
        "session_id": f"liaison-{chat_id}",
    }

    # Panggil Liaison Agent
    result = await liaison_agent_node(state)
    complaint = result.get("complaint")
    
    # Update data sesi dari hasil ekstraksi AI
    if complaint:
        if complaint["order_id"] != "unknown":
            session.order_id = complaint["order_id"]
        if complaint["complaint_description"] != "unknown":
            session.complaint_text = complaint["complaint_description"]

    # Ambil balasan AI untuk pelanggan
    # Kita butuh mengambil output JSON asli dari Liaison untuk mendapatkan 'customer_response'
    # Karena liaison_agent_node mengembalikan dict dengan 'complaint' dan 'messages'
    llm_message = result["messages"][0].content
    
    # Ekstraksi JSON dari response
    import json, re
    json_match = re.search(r"({.*})", llm_message, re.DOTALL)
    ai_data = json.loads(json_match.group(1)) if json_match else {}
    
    ai_reply = ai_data.get("customer_response", "Maaf, bisa diulangi?")
    is_complete = ai_data.get("data_complete", False)

    # Kirim balasan interaktif AI ke Telegram
    await update.message.reply_text(ai_reply, parse_mode=ParseMode.MARKDOWN)

    # Jika AI merasa data sudah lengkap, lanjut ke tahap berikutnya
    if is_complete and session.order_id != "unknown":
        # Cek apakah butuh foto?
        skip_photo_keywords = ["telat", "lambat", "lama", "kosong", "habis", "refund", "dana", "kembali", "uang"]
        needs_photo = not any(kw in session.complaint_text.lower() for kw in skip_photo_keywords)

        if needs_photo:
            session.step = ConversationStep.WAITING_PHOTO
            await update.message.reply_text(ASK_PHOTO_MSG, parse_mode=ParseMode.MARKDOWN)
        else:
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
    
    from src.logger import broadcast_event
    broadcast_event("session_start", session_id, {"project_name": "OmniResolve-AI"})

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
        audit = final_state.get("audit_result")

        # Simpan ke DB untuk Dashboard Admin
        from src.api.routers.complaints import save_session_to_db
        await save_session_to_db(session_id, pipeline_input, final_state)

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
            # Emoji berdasarkan tipe keputusan
            type_emoji = {
                "replacement": "🔄 Ganti Baru",
                "refund": "💰 Pengembalian Dana",
                "voucher": "🎫 Voucher Kompensasi",
                "reject": "❌ Klaim Ditolak",
            }
            decision_label = type_emoji.get(decision['decision_type'], decision['decision_type'])

            # Tampilkan status audit
            audit_status = ""
            if audit:
                claim_icon = "✅" if audit.get("claim_valid") else "⛔"
                audit_status = f"\n• Validasi klaim: {claim_icon} {'Valid' if audit.get('claim_valid') else 'Tidak Valid'}"

            detail_text = (
                f"📋 *Detail Keputusan:*\n"
                f"• Tipe: {decision_label}\n"
                f"• Nilai kompensasi: Rp {decision['compensation_value_idr']:,.0f}"
                f"{audit_status}\n"
                f"• Ref: `{session_id}`\n\n"
                f"💡 _Anda dapat memantau status atau detail tindak lanjut laporan ini kapan saja dengan mengetik:_ `/status {session_id}`"
            )
            if decision.get("requires_human_approval"):
                detail_text += "\n\n⚠️ _Kasus ini memerlukan persetujuan supervisor karena nilai kompensasi melebihi batas otomatis. Kami akan menghubungi Anda dalam 1x24 jam._"

            await context.bot.send_message(
                chat_id=chat_id,
                text=detail_text,
                parse_mode=ParseMode.MARKDOWN,
            )

            # Kirim perintah pengambilan barang ke Gudang secara otomatis jika merupakan replacement dan di bawah 1 juta (tidak butuh human approval)
            if decision['decision_type'] == 'replacement' and not decision.get("requires_human_approval") and session.order_id and session.order_id != "unknown":
                await send_to_warehouse_group(context, session_id, session.order_id)

        # Tombol untuk komplain baru
        keyboard = [[InlineKeyboardButton("🔄 Komplain Baru", callback_data="new_complaint")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=chat_id,
            text="Ada keluhan lain yang bisa kami bantu?",
            reply_markup=reply_markup,
        )

        # Simpan info untuk AWAITING_CHOICE dan arahkan pelanggan
        session.last_session_id = session_id
        session.last_decision_type = decision.get('decision_type', '') if decision else ''

        # Jika ada pilihan untuk pelanggan (voucher/reject → tawarkan 1 atau 2)
        if decision and decision.get('decision_type') in ('voucher', 'reject'):
            session.step = ConversationStep.AWAITING_CHOICE
        else:
            session.step = ConversationStep.DONE

        broadcast_event("session_end", session_id, {"project_name": "OmniResolve-AI"})
        logger.info("telegram.pipeline_done", chat_id=chat_id, session_id=session_id)

    except Exception as e:
        logger.error("telegram.pipeline_error", chat_id=chat_id, error=str(e))
        await processing_msg.delete()
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "✅ *Laporan Keluhan Tercatat*\n\n"
                "Sistem kami telah mencatat laporan keluhan Anda dengan kode referensi:\n"
                f"`{session_id}`\n\n"
                "💡 *Tips:* Silakan salin kode referensi di atas. Anda dapat memeriksa status tindak lanjut, detail keputusan, serta follow-up dari perusahaan kapan saja dengan mengetik:\n"
                f"`/status {session_id}`\n\n"
                "Tim kami sedang memproses penyelesaian laporan Anda."
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        session.step = ConversationStep.DONE
        broadcast_event("session_end", session_id, {"project_name": "OmniResolve-AI"})


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
    elif query.data == "status_last":
        chat_id = update.effective_chat.id
        session = session_manager.get(chat_id)
        # Query status keluhan terakhir milik pelanggan ini
        success = await query_and_send_status(chat_id, None, query)
        if success:
            session.step = ConversationStep.DONE
        else:
            session.step = ConversationStep.GREETING
    elif query.data == "status_cancel":
        chat_id = update.effective_chat.id
        session = session_manager.get(chat_id)
        session.step = ConversationStep.GREETING
        await query.message.edit_text(
            "🚫 Pelacakan status dibatalkan. Ketik /start jika Anda ingin berinteraksi kembali.",
            parse_mode=ParseMode.MARKDOWN
        )
    elif query.data.startswith("wh_done:"):
        parts = query.data.split(":")
        session_id = parts[1]
        order_id = parts[2]
        
        # Ambil detail dari database PostgreSQL
        settings = get_settings()
        import asyncpg
        from datetime import datetime
        
        try:
            conn = await asyncpg.connect(
                user=settings.postgres_user,
                password=settings.postgres_password,
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_db
            )
            
            query_details = """
                SELECT c.customer_name, c.phone, c.address, p.product_name, oi.quantity
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                JOIN order_items oi ON o.order_id = oi.order_id
                JOIN products p ON oi.product_id = p.product_id
                WHERE o.order_id = $1
            """
            rows = await conn.fetch(query_details, order_id)
            await conn.close()
            
            if rows:
                customer_name = rows[0]["customer_name"]
                phone = rows[0]["phone"]
                address = rows[0]["address"]
                
                # Format daftar produk
                items_list = ""
                for row in rows:
                    items_list += f"• 📦 *{row['product_name']}* - {row['quantity']} unit\n"
                
                # Cek apakah grup kurir terdaftar
                group_data = load_group_chats()
                courier_chat_id = group_data.get("courier_chat_id")
                
                if courier_chat_id:
                    # Kirim pesan ke grup Kurir
                    courier_msg = (
                        f"🚚 *PENGIRIMAN BARANG READY (KURIR)*\n\n"
                        f"Barang pengganti telah selesai disiapkan oleh gudang dan siap dikirim!\n"
                        f"• *Nama Penerima:* {customer_name} ({phone})\n"
                        f"• *Alamat Penerima:* {address}\n"
                        f"• *Nomor Order:* `{order_id}`\n"
                        f"• *Ref Sesi:* `{session_id}`\n\n"
                        f"📦 *Daftar Barang untuk Dikirim:*\n"
                        f"{items_list}\n"
                        f"🚀 _Silakan kurir untuk segera mengambil barang di gudang dan mengantarkannya ke alamat penerima._"
                    )
                    await context.bot.send_message(
                        chat_id=courier_chat_id,
                        text=courier_msg,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                    # Update pesan di grup gudang menjadi hijau/sukses
                    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    sender_username = query.from_user.username or query.from_user.first_name
                    
                    warehouse_updated_msg = (
                        f"✅ *Barang Telah Disiapkan oleh Gudang & Siap Kirim*\n\n"
                        f"• *Petugas Gudang:* @{sender_username}\n"
                        f"• *Waktu Selesai:* {timestamp}\n"
                        f"• *Penerima:* {customer_name} ({phone})\n"
                        f"• *Nomor Order:* `{order_id}`\n\n"
                        f"📋 *Daftar Barang:* \n"
                        f"{items_list}\n"
                        f"📍 *Status:* _Instruksi pengiriman telah dikirim otomatis ke grup Kurir._"
                    )
                    await query.message.edit_text(
                        text=warehouse_updated_msg,
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await query.message.reply_text(
                        "⚠️ *Grup Kurir belum terdaftar!* Silakan daftarkan grup kurir terlebih dahulu dengan command `/register_kurir` di dalam grup kurir.",
                        parse_mode=ParseMode.MARKDOWN
                    )
            else:
                await query.message.reply_text("⚠️ Data order tidak ditemukan di sistem.")
                
        except Exception as e:
            logger.error("telegram.wh_done_callback_error", error=str(e))
            await query.message.reply_text("⚠️ Terjadi kesalahan saat memproses status gudang.")
    elif query.data.startswith("faq_"):
        ans = ""
        if query.data == "faq_return":
            ans = "Syarat Retur: Maksimal 3 hari sejak barang diterima, harus disertakan video unboxing utuh tanpa terputus."
        elif query.data == "faq_hours":
            ans = "Jam Operasional Qhomemart:\nSenin - Minggu, 08:00 - 21:00 WIB."
        elif query.data == "faq_tracking":
            ans = "Lacak Pengiriman: Anda bisa mengecek resi secara langsung di website kargo terkait, atau tanyakan kepada bot ini dengan format pesan menyertakan ORD-XXX."
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"💡 *Info FAQ:*\n{ans}",
            parse_mode=ParseMode.MARKDOWN
        )
