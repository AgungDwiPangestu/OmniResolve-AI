# CLAUDE.md — OmniResolve-AI

Dokumen ini membantu AI (Claude/Antigravity) memahami konteks proyek secara menyeluruh sebelum mengerjakan tugas apa pun.

---

## Ringkasan Proyek

**OmniResolve-AI** adalah sistem multi-agent berbasis **LangGraph** untuk otomatisasi penyelesaian komplain pelanggan e-commerce **Qhomemart** (toko bahan bangunan & peralatan rumah tangga). Sistem menerima keluhan via Telegram Bot, memprosesnya melalui pipeline 4 agen AI, dan menghasilkan keputusan (penggantian, voucher, atau eskalasi ke manusia) secara otomatis.

---

## Arsitektur & Komponen

### Pipeline Multi-Agent (LangGraph)

```
Pelanggan Telegram
       │
       ▼
[1] Liaison Agent        → Ekstrak order_id, nama, deskripsi keluhan
       │
       ▼
[2] Logistics Auditor    → Verifikasi pengiriman: kondisi gudang + kurir
       │  (retry loop jika data tidak cukup)
       ▼
[3] Strategic Negotiator → Tentukan keputusan: replacement / voucher / reject
       │
       ├─── (nilai > Rp 1jt) ──► [HITL] hitl_supervisor_node → kirim email + END
       │
       ▼
[4] Supply Chain Orchestrator → Eksekusi: notif gudang, kurir, atau voucher → END
```

**File workflow:** `src/graph/workflow.py`  
**State graph:** `src/graph/state.py`

### Agen

| File | Peran |
|------|-------|
| `src/agents/liaison_agent.py` | Ekstrak data keluhan dari teks bebas pelanggan |
| `src/agents/logistics_auditor.py` | Cek status pengiriman & kondisi barang di gudang (dengan retry loop self-correction) |
| `src/agents/strategic_negotiator.py` | Negosiasi & tentukan keputusan kompensasi sesuai SOP Qhomemart |
| `src/agents/supply_chain_orchestrator.py` | Eksekusi keputusan: notifikasi gudang/kurir via Telegram group + HITL email |

### Tools (Alat Database)

| File | Fungsi |
|------|--------|
| `src/tools/erp_tools.py` | Query data pelanggan, order, dan order items dari PostgreSQL |
| `src/tools/courier_tools.py` | Query status pengiriman dan delivery logs dari tabel `deliveries` |
| `src/tools/inventory_tools.py` | Cek stok dan kondisi produk di gudang |
| `src/tools/vector_store.py` | Vector search menggunakan pgvector + LangChain embedding |

### Telegram Bot

| File | Fungsi |
|------|--------|
| `src/telegram_bot/handlers.py` | Handler semua pesan: teks, foto, command, callback query |
| `src/telegram_bot/session.py` | Manajemen state percakapan per pelanggan (in-memory) |
| `src/telegram_bot/group_chats.json` | Menyimpan chat_id grup Gudang & Kurir yang terdaftar |

#### ConversationStep (State Machine Pelanggan)

```
GREETING → GATHERING → WAITING_PHOTO → PROCESSING → AWAITING_CHOICE → DONE
                                                   ↘
                                                    ESCALATED
```

- `AWAITING_CHOICE`: Menunggu pelanggan ketik **1** (terima voucher) atau **2** (minta surat resmi)
- Setelah pipeline selesai dengan keputusan `voucher` atau `reject`, state otomatis masuk `AWAITING_CHOICE`

### API Backend

- **Framework:** FastAPI (async)
- **Entry point:** `src/api/main.py` (port 8000)
- **WebSocket:** `/ws/{session_id}` untuk live update ke Visualizer

### Visualizer

- **Path:** `visualizer/`
- **Tech:** FastAPI backend + React/TypeScript frontend
- **Port:** 8001 (container internal: 8002)
- **Fungsi:** Dashboard real-time monitoring pipeline agent via WebSocket

---

## Stack Teknologi

| Komponen | Teknologi |
|----------|-----------|
| Orkestrasi agen | LangGraph (`langgraph`) |
| LLM | Claude 3 Haiku via SumoPod API (OpenAI-compatible) |
| Database | PostgreSQL 16 + pgvector extension |
| ORM / DB driver | `asyncpg` (async), `sqlalchemy` (sync untuk pgvector) |
| Backend API | FastAPI + uvicorn |
| Bot | `python-telegram-bot` v20+ (async) |
| Logging | `structlog` (structured JSON logging) |
| Config | `pydantic-settings` (baca dari `.env`) |
| Container | Docker Compose / Podman Compose |
| Embedding | `text-embedding-3-small` via SumoPod |

---

## Database Schema

### Tabel Utama

```sql
customers     → data pelanggan (CLV, total_orders, is_loyal, previous_complaints)
products      → katalog produk (harga, stok, warehouse_condition)
orders        → data transaksi
order_items   → item per order
deliveries    → log pengiriman (condition_on_pickup, damage_reported_by_courier, delivery_logs JSONB)
```

### Tabel Sistem

```sql
complaint_sessions    → hasil pipeline (decision_type, compensation_value_idr, requires_human_approval)
langchain_pg_collection / langchain_pg_embedding  → vector store untuk RAG
```

### Nilai Penting di `deliveries`

- `condition_on_pickup = 'damaged_at_pickup'` → kerusakan dari gudang (klaim valid)
- `condition_on_pickup = 'intact'` + `damage_reported_by_courier = TRUE` → rusak saat transit (klaim valid)
- `condition_on_pickup = 'intact'` + `damage_reported_by_courier = FALSE` → pengiriman bersih (klaim diragukan)

---

## Business Logic (SOP Qhomemart)

| Kondisi | Keputusan AI |
|---------|--------------|
| Kerusakan fisik + bukti logistik valid | `replacement` (penggantian barang) |
| Barang hilang / salah kirim | `refund` |
| Stok kosong, tidak bisa ganti | `refund` |
| Keluhan valid tapi minor | `voucher` (kompensasi) |
| Klaim tidak terbukti | `reject` |
| Kompensasi > Rp 1.000.000 | Wajib persetujuan supervisor (HITL via email) |

**CLV (Customer Lifetime Value):** Total belanja pelanggan sepanjang masa. Pelanggan CLV tinggi mendapat prioritas penanganan lebih baik.

---

## Environment Variables Penting

```env
# LLM
LLM_BASE_URL=https://api.sumopod.com/v1
LLM_API_KEY=...
LLM_MODEL_NAME=claude-3-haiku-20240307

# Database
POSTGRES_HOST=postgres
POSTGRES_DB=omni_resolve
POSTGRES_USER=omni_user
POSTGRES_PASSWORD=...

# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_MODE=polling        # "polling" (lokal) | "webhook" (produksi)
TELEGRAM_ADMIN_CHAT_ID=...   # Chat ID supervisor HITL

# App
ENVIRONMENT=development      # atau "production"
BASE_URL=http://localhost:8001  # URL publik (produksi: https://omniresolve.pixelwar.tech)
HITL_THRESHOLD_IDR=1000000   # Threshold approval supervisor (Rp 1jt)

# SMTP (notifikasi email HITL)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASS=...
```

---

## Perintah Development

### Jalankan Lokal (Podman)

```bash
# Start semua service
podman compose up -d

# Rebuild setelah perubahan kode
podman compose build api && podman compose up -d api

# Lihat log
podman compose logs -f api

# Seed ulang database
podman exec -i omni_postgres psql -U omni_user -d omni_resolve < db/seed.sql
```

### Jalankan Lokal (Docker)

```bash
docker compose up -d
docker compose build api && docker compose up -d api
docker exec -i omni_postgres psql -U omni_user -d omni_resolve < db/seed.sql
```

### Database

```bash
# Akses psql langsung
podman exec -it omni_postgres psql -U omni_user -d omni_resolve

# Query cepat cek delivery bermasalah
SELECT order_id, condition_on_pickup, damage_reported_by_courier FROM deliveries
WHERE condition_on_pickup = 'damaged_at_pickup' OR damage_reported_by_courier = TRUE;
```

---

## Deployment Produksi (VPS)

- **VPS:** 43.134.7.92
- **Domain API:** https://omniresolve.pixelwar.tech
- **Domain Visualizer:** https://visualizer.pixelwar.tech (jika dikonfigurasi)
- **Nginx:** Reverse proxy ke port 8000 (API) dan 8001 (Visualizer)
  - `/api/` → backend port 8000
  - `/ws/` → WebSocket dengan `proxy_read_timeout 86400;`
- **Container runtime:** Docker

```bash
# Update ke VPS setelah push
git pull origin main
docker compose build api
docker compose up -d
docker exec -i omni_postgres psql -U omni_user -d omni_resolve < db/seed.sql
```

---

## Struktur Direktori

```
OmniResolve-AI/
├── db/
│   ├── init.sql              # Skema database (CREATE TABLE, index, trigger)
│   └── seed.sql              # 70 data dummy Qhomemart (customers, orders, deliveries)
├── src/
│   ├── agents/               # 4 agen LangGraph
│   ├── api/                  # FastAPI routes + WebSocket
│   ├── graph/
│   │   ├── state.py          # GraphState dataclass
│   │   └── workflow.py       # LangGraph StateGraph builder
│   ├── telegram_bot/
│   │   ├── handlers.py       # Semua handler Telegram (907 baris)
│   │   └── session.py        # ConversationStep state machine
│   ├── tools/                # Database query tools untuk agen
│   ├── config.py             # Settings via pydantic-settings
│   └── logger.py             # Structlog setup
├── visualizer/               # Dashboard monitoring (FastAPI + React)
├── docker-compose.yml
├── docker-compose.override.yml  # Override untuk dev (hot-reload)
├── Dockerfile
└── .env                      # Konfigurasi aktif (jangan di-commit)
```

---

## Hal yang Perlu Diperhatikan

1. **Session bot bersifat in-memory** — restart container akan reset semua sesi aktif pelanggan
2. **Group chats disimpan di file JSON** (`src/telegram_bot/group_chats.json`) — pastikan file ini tidak hilang saat container rebuild
3. **Webhook vs Polling** — lokal gunakan `TELEGRAM_MODE=polling`; produksi gunakan `webhook` dengan `BASE_URL` yang benar
4. **HITL threshold** — default Rp 1.000.000; ubah via `HITL_THRESHOLD_IDR` di `.env`
5. **pgvector** — membutuhkan image `pgvector/pgvector:pg16`, bukan postgres biasa
6. **Seed data** — seed ulang akan **TRUNCATE CASCADE** semua tabel ERP; data `complaint_sessions` aman karena menggunakan `ON CONFLICT DO NOTHING`
