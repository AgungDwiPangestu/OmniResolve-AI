"""
src/tools/vector_store.py — pgvector Integration untuk Policy Documents

Menyimpan dan mencari dokumen kebijakan perusahaan menggunakan pgvector.
Digunakan oleh agen untuk referensi policy saat pengambilan keputusan.
"""
import structlog
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document

from src.config import get_settings

logger = structlog.get_logger(__name__)

COLLECTION_NAME = "company_policies"


def get_embeddings():
    """Inisialisasi embedding model dari SumoPod API."""
    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.embedding_model_name,
        openai_api_key=settings.embedding_api_key,
        openai_api_base=settings.embedding_base_url,
    )


def get_vector_store() -> PGVector:
    """
    Inisialisasi PGVector store.
    pgvector adalah ekstensi PostgreSQL — tidak butuh service terpisah.
    """
    settings = get_settings()
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=COLLECTION_NAME,
        connection=settings.database_url_sync,
        use_jsonb=True,
    )


async def search_policy(query: str, k: int = 3) -> list[Document]:
    """
    Cari dokumen kebijakan yang relevan dengan query.
    Digunakan oleh Negotiator untuk referensi policy kompensasi.
    """
    try:
        vector_store = get_vector_store()
        docs = vector_store.similarity_search(query, k=k)
        logger.info("vector_store.search", query=query[:50], results=len(docs))
        return docs
    except Exception as e:
        logger.error("vector_store.search_error", error=str(e))
        return []


async def ingest_policies(policy_texts: list[dict]) -> int:
    """
    Ingest dokumen kebijakan ke pgvector.
    Dipanggil sekali saat setup atau ketika ada update policy.

    policy_texts: [{"content": "...", "metadata": {"category": "...", "version": "..."}}]
    """
    docs = [
        Document(
            page_content=p["content"],
            metadata=p.get("metadata", {}),
        )
        for p in policy_texts
    ]

    try:
        vector_store = get_vector_store()
        vector_store.add_documents(docs)
        logger.info("vector_store.ingested", count=len(docs))
        return len(docs)
    except Exception as e:
        logger.error("vector_store.ingest_error", error=str(e))
        return 0


# --- Sample policies untuk seeding ---
SAMPLE_POLICIES = [
    {
        "content": (
            "Kebijakan kompensasi barang rusak: Jika barang terbukti rusak saat pengiriman "
            "dan pelanggan telah mengirimkan bukti foto, maka pelanggan berhak mendapatkan "
            "penggantian barang baru atau refund penuh sesuai pilihan pelanggan."
        ),
        "metadata": {"category": "compensation", "version": "v2.1"},
    },
    {
        "content": (
            "Kebijakan pelanggan setia: Pelanggan dengan total pembelian di atas Rp 5.000.000 "
            "dikategorikan sebagai pelanggan setia dan berhak mendapatkan layanan prioritas, "
            "termasuk pengiriman pengganti dalam 24 jam tanpa biaya tambahan."
        ),
        "metadata": {"category": "loyalty", "version": "v1.3"},
    },
    {
        "content": (
            "Batas kompensasi otomatis: Sistem dapat menyetujui kompensasi hingga Rp 1.000.000 "
            "secara otomatis. Kompensasi di atas batas ini memerlukan persetujuan supervisor "
            "atau manajer layanan pelanggan."
        ),
        "metadata": {"category": "authorization", "version": "v3.0"},
    },
    {
        "content": (
            "Kebijakan klaim tidak valid: Jika audit menunjukkan bahwa kerusakan terjadi "
            "setelah barang diterima (misalnya, kerusakan akibat penggunaan yang tidak sesuai), "
            "maka klaim akan ditolak. Pelanggan akan diberikan penjelasan dan tautan ke garansi resmi."
        ),
        "metadata": {"category": "rejection", "version": "v1.0"},
    },
]
