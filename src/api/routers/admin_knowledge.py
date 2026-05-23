"""
src/api/routers/admin_knowledge.py — Admin Knowledge Base Management API

Endpoint untuk mengelola RAG Knowledge Base secara manual:

  POST   /api/v1/admin/knowledge/seed          → Seed semua collection dengan data awal
  GET    /api/v1/admin/knowledge/stats          → Statistik jumlah dokumen per collection
  POST   /api/v1/admin/knowledge/ingest         → Upload dokumen baru ke collection tertentu
  DELETE /api/v1/admin/knowledge/{collection}   → Hapus semua dokumen dari collection tertentu

CATATAN KEAMANAN:
  Endpoint ini tidak memerlukan autentikasi di mode development.
  Di production, lindungi endpoint ini dengan API key atau middleware auth.
  Contoh: tambahkan dependency `Depends(verify_admin_key)` ke setiap route.
"""
import io
import structlog
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from src.tools.knowledge_ingestion import seed_initial_knowledge, ingest_manual_documents
from src.tools.vector_store import get_vector_store, COLLECTIONS

logger = structlog.get_logger(__name__)

router = APIRouter()


# --- Request/Response Models ---

class IngestRequest(BaseModel):
    collection: str = Field(
        ...,
        description="Target collection. Pilihan: sop_policies, faq_patterns, product_catalog, resolved_cases",
        examples=["sop_policies"],
    )
    documents: list[dict] = Field(
        ...,
        description="List dokumen. Setiap item harus punya key 'content' (str) dan optional 'metadata' (dict).",
        examples=[[{"content": "Kebijakan baru...", "metadata": {"category": "policy"}}]],
    )


class IngestResponse(BaseModel):
    collection: str
    ingested_count: int
    message: str


class SeedResponse(BaseModel):
    message: str
    results: dict[str, int]
    total_ingested: int


class StatsResponse(BaseModel):
    collections: dict[str, dict]


class DeleteResponse(BaseModel):
    collection: str
    message: str


# --- Endpoints ---

@router.post(
    "/admin/knowledge/seed",
    response_model=SeedResponse,
    summary="Seed Knowledge Base",
    description=(
        "Isi semua collection dengan data awal (SOP Qhomemart, FAQ, katalog produk). "
        "Aman dijalankan berulang kali. Wajib dijalankan sekali setelah setup pertama kali."
    ),
    tags=["Knowledge Base (RAG)"],
)
async def seed_knowledge():
    """Seed semua collection dengan initial data."""
    try:
        results = await seed_initial_knowledge()
        total = sum(results.values())
        logger.info("admin.seed_knowledge", results=results)
        return SeedResponse(
            message="Knowledge base berhasil di-seed.",
            results=results,
            total_ingested=total,
        )
    except Exception as e:
        logger.error("admin.seed_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Seed gagal: {e}")


@router.get(
    "/admin/knowledge/stats",
    response_model=StatsResponse,
    summary="Statistik Knowledge Base",
    description="Tampilkan jumlah dokumen dan deskripsi setiap collection.",
    tags=["Knowledge Base (RAG)"],
)
async def get_knowledge_stats():
    """Ambil statistik dokumen per collection."""
    stats = {}
    for collection_name, description in COLLECTIONS.items():
        try:
            store = get_vector_store(collection_name)
            # PGVector menyimpan di tabel langchain_pg_embedding
            # Cara paling reliable: query via store._session
            count = len(store.similarity_search("*", k=9999))
        except Exception:
            count = -1  # -1 artinya tidak bisa dihitung (collection kosong atau error)

        stats[collection_name] = {
            "description": description,
            "document_count": count,
        }

    return StatsResponse(collections=stats)


@router.post(
    "/admin/knowledge/ingest",
    response_model=IngestResponse,
    summary="Upload Dokumen ke Knowledge Base",
    description=(
        "Tambahkan dokumen baru ke collection tertentu. "
        "Berguna untuk menambahkan SOP baru, FAQ, atau informasi produk."
    ),
    tags=["Knowledge Base (RAG)"],
)
async def ingest_documents_endpoint(payload: IngestRequest):
    """Upload dokumen baru ke collection tertentu."""
    if payload.collection not in COLLECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Collection '{payload.collection}' tidak valid. Pilihan: {list(COLLECTIONS.keys())}",
        )

    if not payload.documents:
        raise HTTPException(status_code=400, detail="Daftar dokumen tidak boleh kosong.")

    # Validasi: setiap dokumen harus punya 'content'
    for i, doc in enumerate(payload.documents):
        if "content" not in doc or not doc["content"].strip():
            raise HTTPException(
                status_code=400,
                detail=f"Dokumen ke-{i + 1} tidak punya key 'content' atau isinya kosong.",
            )

    try:
        count = await ingest_manual_documents(payload.documents, collection=payload.collection)
        logger.info("admin.ingest", collection=payload.collection, count=count)
        return IngestResponse(
            collection=payload.collection,
            ingested_count=count,
            message=f"{count} dokumen berhasil ditambahkan ke collection '{payload.collection}'.",
        )
    except Exception as e:
        logger.error("admin.ingest_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Ingest gagal: {e}")


@router.delete(
    "/admin/knowledge/{collection}",
    response_model=DeleteResponse,
    summary="Hapus Semua Dokumen dari Collection",
    description=(
        "Hapus seluruh dokumen dari collection tertentu. "
        "PERHATIAN: Operasi ini tidak bisa dibatalkan."
    ),
    tags=["Knowledge Base (RAG)"],
)
async def clear_collection(collection: str):
    """Hapus semua dokumen dari collection tertentu."""
    if collection not in COLLECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Collection '{collection}' tidak valid. Pilihan: {list(COLLECTIONS.keys())}",
        )

    try:
        store = get_vector_store(collection)
        store.delete_collection()
        logger.info("admin.clear_collection", collection=collection)
        return DeleteResponse(
            collection=collection,
            message=f"Semua dokumen di collection '{collection}' telah dihapus.",
        )
    except Exception as e:
        logger.error("admin.clear_error", collection=collection, error=str(e))
        raise HTTPException(status_code=500, detail=f"Gagal menghapus collection: {e}")


def _extract_text_from_file(filename: str, content: bytes) -> str:
    """Parse file content based on extension. Supports txt, md, pdf, docx."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("txt", "md"):
        return content.decode("utf-8", errors="replace")

    if ext == "pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            raise HTTPException(status_code=500, detail="pypdf tidak terinstall di server.")
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(p for p in pages if p.strip())
        if not text.strip():
            raise HTTPException(status_code=422, detail="PDF tidak mengandung teks yang bisa diekstrak.")
        return text

    if ext in ("docx", "doc"):
        try:
            from docx import Document
        except ImportError:
            raise HTTPException(status_code=500, detail="python-docx tidak terinstall di server.")
        doc = Document(io.BytesIO(content))
        text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        if not text.strip():
            raise HTTPException(status_code=422, detail="Dokumen tidak mengandung teks yang bisa diekstrak.")
        return text

    raise HTTPException(
        status_code=415,
        detail=f"Format file '.{ext}' tidak didukung. Gunakan: pdf, docx, md, atau txt.",
    )


@router.post(
    "/admin/knowledge/upload",
    response_model=IngestResponse,
    summary="Upload File Dokumen ke Knowledge Base",
    description=(
        "Upload file (PDF, DOCX, Markdown, TXT) dan otomatis parse + ingest ke collection yang dipilih."
    ),
    tags=["Knowledge Base (RAG)"],
)
async def upload_document_file(
    file: UploadFile = File(...),
    collection: str = Form(...),
    category: str = Form(""),
    source: str = Form(""),
):
    if collection not in COLLECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Collection '{collection}' tidak valid. Pilihan: {list(COLLECTIONS.keys())}",
        )

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="File kosong.")

    filename = file.filename or "upload"
    text = _extract_text_from_file(filename, raw)

    metadata: dict = {}
    if category.strip():
        metadata["category"] = category.strip()
    metadata["source"] = source.strip() if source.strip() else filename

    try:
        count = await ingest_manual_documents(
            [{"content": text, "metadata": metadata}],
            collection=collection,
        )
        logger.info("admin.upload_file", filename=filename, collection=collection, count=count)
        return IngestResponse(
            collection=collection,
            ingested_count=count,
            message=f"File '{filename}' berhasil diparse dan {count} chunk ditambahkan ke '{collection}'.",
        )
    except Exception as e:
        logger.error("admin.upload_error", filename=filename, error=str(e))
        raise HTTPException(status_code=500, detail=f"Ingest gagal: {e}")
