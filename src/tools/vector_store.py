"""
src/tools/vector_store.py — Multi-Collection pgvector Knowledge Base

Arsitektur RAG OmniResolve-AI menggunakan 4 collection terpisah:

  sop_policies    → Kebijakan & SOP bisnis Qhomemart (manual admin)
  resolved_cases  → Riwayat kasus komplain yang diselesaikan (auto-generated)
  product_catalog → Info produk, kategori, FAQ produk (sync dari DB)
  faq_patterns    → Pola keluhan umum & respons ideal (manual + auto)

Setiap agen hanya query collection yang relevan dengan tugasnya,
sehingga konteks yang diterima LLM selalu domain-spesifik.
"""
import structlog
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document

from src.config import get_settings

logger = structlog.get_logger(__name__)

# --- 4 collection namespaces ---
COLLECTIONS = {
    "sop_policies": "Kebijakan dan SOP bisnis Qhomemart",
    "resolved_cases": "Riwayat kasus komplain yang berhasil diselesaikan",
    "product_catalog": "Informasi produk, kategori, dan FAQ terkait produk",
    "faq_patterns": "Pola keluhan umum dan respons yang tepat",
}


def get_embeddings() -> OpenAIEmbeddings:
    """Inisialisasi embedding model dari SumoPod API."""
    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.embedding_model_name,
        openai_api_key=settings.embedding_api_key,
        openai_api_base=settings.embedding_base_url,
    )


def get_vector_store(collection: str = "sop_policies") -> PGVector:
    """
    Inisialisasi PGVector store untuk collection tertentu.
    Setiap collection disimpan sebagai tabel terpisah di pgvector.
    """
    if collection not in COLLECTIONS:
        raise ValueError(f"Collection '{collection}' tidak dikenal. Pilihan: {list(COLLECTIONS.keys())}")

    settings = get_settings()
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=collection,
        connection=settings.database_url_sync,
        use_jsonb=True,
    )


async def search_knowledge(query: str, collection: str, k: int = 3) -> list[Document]:
    """
    Cari dokumen yang relevan dari collection tertentu.

    Args:
        query: Teks pencarian (biasanya dari konteks komplain saat ini)
        collection: Nama collection — satu dari COLLECTIONS
        k: Jumlah dokumen teratas yang dikembalikan

    Returns:
        List Document dengan page_content dan metadata
    """
    try:
        store = get_vector_store(collection)
        docs = store.similarity_search(query, k=k)
        logger.info("rag.search", collection=collection, query=query[:60], results=len(docs))
        return docs
    except Exception as e:
        logger.warning("rag.search_error", collection=collection, error=str(e))
        return []


async def ingest_documents(documents: list[dict], collection: str) -> int:
    """
    Ingest dokumen ke collection tertentu.

    Args:
        documents: List dict dengan key 'content' dan optional 'metadata'
        collection: Target collection

    Returns:
        Jumlah dokumen yang berhasil di-ingest

    Example:
        await ingest_documents([
            {"content": "SOP barang rusak...", "metadata": {"category": "compensation"}}
        ], collection="sop_policies")
    """
    if collection not in COLLECTIONS:
        raise ValueError(f"Collection '{collection}' tidak dikenal.")

    docs = [
        Document(
            page_content=d["content"],
            metadata=d.get("metadata", {}),
        )
        for d in documents
    ]

    try:
        store = get_vector_store(collection)
        store.add_documents(docs)
        logger.info("rag.ingested", collection=collection, count=len(docs))
        return len(docs)
    except Exception as e:
        logger.error("rag.ingest_error", collection=collection, error=str(e))
        return 0


# --- Alias untuk backward-compatibility ---
async def search_policy(query: str, k: int = 3) -> list[Document]:
    """Alias lama — query ke sop_policies. Gunakan search_knowledge() untuk kode baru."""
    return await search_knowledge(query, "sop_policies", k=k)


# ---------------------------------------------------------------------------
# Initial seed data untuk setiap collection
# Dipakai oleh: POST /api/v1/admin/knowledge/seed
# ---------------------------------------------------------------------------

SEED_SOP_POLICIES = [
    {
        "content": (
            "Kebijakan kompensasi barang rusak: Jika barang terbukti rusak saat pengiriman "
            "dan pelanggan telah mengirimkan bukti foto, pelanggan berhak mendapatkan "
            "penggantian barang baru (replacement) atau refund penuh sesuai pilihan pelanggan. "
            "Untuk penggantian barang, berikan tambahan voucher diskon Rp 50.000."
        ),
        "metadata": {"category": "compensation", "type": "damaged_item", "version": "v2.1"},
    },
    {
        "content": (
            "Kebijakan pelanggan setia (loyal customer): Pelanggan dengan CLV (Customer Lifetime Value) "
            "di atas Rp 10.000.000 dikategorikan sebagai pelanggan setia dan berhak mendapatkan "
            "layanan prioritas, termasuk pengiriman pengganti dalam 24 jam tanpa biaya tambahan, "
            "serta tambahan Voucher Loyalty Rp 200.000 di luar solusi utama."
        ),
        "metadata": {"category": "loyalty", "version": "v1.3"},
    },
    {
        "content": (
            "Batas kompensasi otomatis (HITL threshold): Sistem dapat menyetujui kompensasi "
            "hingga Rp 1.000.000 secara otomatis tanpa perlu persetujuan supervisor. "
            "Kompensasi di atas batas ini wajib mendapat persetujuan supervisor atau manajer "
            "layanan pelanggan melalui sistem Human-in-the-Loop (HITL)."
        ),
        "metadata": {"category": "authorization", "version": "v3.0"},
    },
    {
        "content": (
            "Kebijakan klaim tidak valid: Jika audit menunjukkan bahwa kerusakan terjadi "
            "setelah barang diterima (misalnya akibat penggunaan tidak sesuai) atau seluruh "
            "bukti logistik menyatakan barang utuh, klaim akan ditolak (reject). "
            "Pelanggan diberikan penjelasan tertulis dan tautan ke garansi resmi produk."
        ),
        "metadata": {"category": "rejection", "version": "v1.0"},
    },
    {
        "content": (
            "Kebijakan salah kirim (wrong item): Jika terbukti terjadi kesalahan pengiriman "
            "produk (produk yang dikirim tidak sesuai pesanan), Qhomemart wajib mengirimkan "
            "ulang produk yang benar (replacement) disertai voucher permintaan maaf Rp 50.000. "
            "Pelanggan tidak perlu mengembalikan barang yang salah kirim."
        ),
        "metadata": {"category": "wrong_item", "version": "v1.2"},
    },
    {
        "content": (
            "Kebijakan stok habis (stock-out): Jika pelanggan sudah membayar namun stok habis "
            "sebelum barang dikirimkan, Qhomemart wajib memberikan dua opsi kepada pelanggan: "
            "(A) Refund penuh 100% harga produk, atau (B) Voucher belanja senilai 110% harga "
            "produk sebagai insentif agar pelanggan tidak menarik uang dan tetap berbelanja."
        ),
        "metadata": {"category": "stock_out", "version": "v2.0"},
    },
    {
        "content": (
            "Kebijakan keterlambatan pengiriman (late delivery): Berikan voucher senilai 10% "
            "dari harga barang jika pengiriman terlambat. Jika keterlambatan lebih dari 5 hari "
            "dari estimasi awal, naikkan kompensasi menjadi 15% dari harga barang. "
            "Tidak ada penggantian barang untuk kasus keterlambatan murni."
        ),
        "metadata": {"category": "late_delivery", "version": "v1.1"},
    },
]

SEED_FAQ_PATTERNS = [
    {
        "content": (
            "Pola keluhan: Pelanggan melaporkan barang datang dalam kondisi pecah, retak, "
            "atau penyok. Kata kunci: 'rusak', 'pecah', 'retak', 'penyok', 'hancur', 'cacat'. "
            "Tipe: damaged_item. Respons yang tepat: empati tinggi, minta bukti foto, "
            "konfirmasi akan diproses dalam 1x24 jam, siapkan opsi replacement atau refund."
        ),
        "metadata": {"pattern_type": "damaged_item", "keywords": "rusak pecah retak"},
    },
    {
        "content": (
            "Pola keluhan: Pelanggan mengaku tidak menerima barang padahal status pengiriman "
            "sudah tertulis 'delivered'. Kata kunci: 'belum sampai', 'tidak terima', "
            "'hilang', 'tidak ada'. Tipe: missing_item. Respons: verifikasi alamat pengiriman, "
            "cek log kurir, koordinasi dengan pihak ekspedisi dalam 2x24 jam."
        ),
        "metadata": {"pattern_type": "missing_item", "keywords": "hilang tidak sampai"},
    },
    {
        "content": (
            "Pola keluhan: Pelanggan menerima produk yang tidak sesuai dengan pesanan. "
            "Kata kunci: 'salah produk', 'beda warna', 'beda ukuran', 'tidak sesuai pesanan'. "
            "Tipe: wrong_item. Respons: minta foto produk yang diterima, proses pengiriman "
            "ulang produk yang benar tanpa biaya tambahan."
        ),
        "metadata": {"pattern_type": "wrong_item", "keywords": "salah produk beda warna"},
    },
    {
        "content": (
            "Pola keluhan: Pelanggan mengeluh pengiriman sangat lambat. "
            "Kata kunci: 'terlambat', 'lama', 'sudah berapa hari', 'kapan sampai', 'belum datang'. "
            "Tipe: late_delivery. Respons: cek log kurir, berikan estimasi baru, "
            "kompensasi voucher 10-15% dari harga barang sesuai durasi keterlambatan."
        ),
        "metadata": {"pattern_type": "late_delivery", "keywords": "terlambat lama belum datang"},
    },
    {
        "content": (
            "Pola pertanyaan non-komplain yang harus DIABAIKAN oleh agen: "
            "pertanyaan di luar lingkup Qhomemart seperti cuaca, politik, resep masakan, "
            "obrolan umum, atau topik tidak berkaitan dengan pesanan dan keluhan belanja. "
            "Respons standar: 'Saya hanya dapat membantu terkait pesanan dan keluhan belanja "
            "di Qhomemart. Silakan hubungi kami dengan nomor order Anda.'"
        ),
        "metadata": {"pattern_type": "off_topic", "keywords": "off-topic guardrail"},
    },
]

SEED_PRODUCT_CATALOG = [
    {
        "content": (
            "Kategori produk Qhomemart: Bahan Bangunan (semen, bata, pasir, besi), "
            "Peralatan Rumah Tangga (furnitur, lemari, meja, kursi), Sanitasi (kloset, wastafel, shower), "
            "Cat & Finishing (cat tembok, cat kayu, thinner), Listrik & Elektronik (kabel, saklar, lampu). "
            "Semua produk dilengkapi garansi resmi dari produsen."
        ),
        "metadata": {"category": "product_categories"},
    },
    {
        "content": (
            "Kebijakan garansi produk Qhomemart: Produk elektronik bergaransi 1 tahun dari tanggal pembelian. "
            "Furnitur bergaransi 6 bulan untuk kerusakan material/produksi. Produk sanitasi bergaransi "
            "1 tahun. Garansi tidak berlaku untuk kerusakan akibat penggunaan tidak sesuai petunjuk "
            "atau modifikasi oleh pelanggan."
        ),
        "metadata": {"category": "warranty_policy"},
    },
    {
        "content": (
            "Proses pemesanan di Qhomemart: Pelanggan memilih produk → checkout → pembayaran → "
            "order dikonfirmasi (status: confirmed) → pengemasan di gudang (status: packing) → "
            "serah terima ke kurir (status: shipped) → pengiriman → terima barang (status: delivered). "
            "Nomor order menggunakan format ORD-XXXXX. Waktu pengiriman standar 2-5 hari kerja."
        ),
        "metadata": {"category": "order_process"},
    },
]
