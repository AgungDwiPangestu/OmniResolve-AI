#  OmniResolve-AI

**Autonomous Omni-Channel Retail Concierge & Conflict Resolver**

Sistem Multi-Agent berbasis **ReAct (Reason + Act)** + **LangGraph** untuk automasi resolusi konflik pelanggan dan optimalisasi inventaris real-time di industri ritel.

---

## 🏗 Arsitektur

```
Pelanggan (via Telegram Bot)
    │
    ▼
[A] Liaison Agent          ← Sentiment analysis + entity extraction
    │
    ▼
[B] Logistics Auditor      ← Cross-check CCTV, kurir, stok (self-correction loop)
    │
    ▼
[C] Strategic Negotiator   ← CLV-based decision (voucher / replacement / refund)
    │
    ├─ (HITL)─▶ Supervisor Notification (jika kompensasi > Rp 1.000.000)
    │
    ▼
[D] Supply Chain Orchestrator  ← ERP update + dispatch kurir + trigger PO
```

## ✨ Key Features

| Feature | Deskripsi |
|---|---|
| **Collaborative Reasoning** | 4 agen saling berbagi state via LangGraph State-Graph |
| **Self-Correction** | Auditor dapat loop kembali jika data belum conclusive |
| **CLV-Based Decisions** | Keputusan kompensasi berbasis Customer Lifetime Value |
| **Human-in-the-Loop** | Auto-notifikasi supervisor untuk kompensasi > Rp 1.000.000 |
| **Traceability (CoT)** | Setiap keputusan memiliki Chain of Thought yang dapat diinspeksi |
| **Telegram Bot** | Interface pelanggan via Telegram (polling/webhook) |
| **OpenAI-Compatible API** | Backend compatible dengan berbagai frontend AI |

## ⚙️ Tech Stack

| Layer | Teknologi |
|---|---|
| **Orchestration** | LangGraph (Stateful Multi-Agent) |
| **LLM** | SumoPod API Marketplace (Anthropic Claude / GLM — OpenAI-compatible) |
| **Vector DB** | pgvector (PostgreSQL extension) |
| **Database** | PostgreSQL 16 |
| **API** | FastAPI + Swagger |
| **Interface** | Telegram Bot (python-telegram-bot v21) |
| **Container** | Docker / Podman (kompatibel, SELinux-aware) |
| **Deployment** | SumoPod |

---

## 🚀 Quick Start

### Prerequisites

- Podman atau Docker
- `podman-compose` atau `docker compose`
- API key dari [SumoPod Marketplace](https://sumopod.com)
- Telegram Bot token dari [@BotFather](https://t.me/BotFather)

### 1. Clone & Setup Environment

```bash
git clone https://github.com/AgungDwiPangestu/OmniResolve-AI.git
cd OmniResolve-AI

# Buat file .env dari template
cp .env.example .env
```

Edit `.env` dan isi variabel berikut (minimal):

```env
# LLM — dari SumoPod API Marketplace
LLM_BASE_URL=https://api.sumopod.com/v1
LLM_API_KEY=your-sumopod-api-key
LLM_MODEL_NAME=claude-3-haiku-20240307

# Telegram Bot — dari @BotFather
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_MODE=polling   # polling untuk dev, webhook untuk production
```

---

## 🐳 Menjalankan Container

### ▶️ Start — Pertama Kali atau Setelah Update Kode

> Gunakan `--build` untuk rebuild image saat ada perubahan kode atau `requirements.txt`

**Podman:**
```bash
podman-compose up --build -d
```

**Docker:**
```bash
docker compose up --build -d
```

Flag `-d` artinya *detached* (berjalan di background).

---

### ▶️ Start — Tanpa Rebuild (Container Sudah Ada)

Jika kode **tidak berubah** dan hanya ingin menghidupkan kembali container yang sudah di-build:

**Podman:**
```bash
podman-compose up -d
```

**Docker:**
```bash
docker compose up -d
```

---

### 🔄 Restart Container

Gunakan saat sudah mengubah **`.env`** (misal: mengisi API key baru) tanpa perlu rebuild image:

**Restart semua service:**

```bash
# Podman
podman-compose restart

# Docker
docker compose restart
```

**Restart satu service saja (misal: hanya API):**

```bash
# Podman
podman-compose restart api

# Docker
docker compose restart api
```

---

### ⏹️ Stop Container

```bash
# Podman
podman-compose down

# Docker
docker compose down
```

> `down` menghentikan dan menghapus container, tapi **data PostgreSQL tetap aman** di volume `postgres_data`.

---

### 🗑️ Reset Total (hapus data + rebuild dari awal)

```bash
# Podman
podman-compose down -v && podman-compose up --build -d

# Docker
docker compose down -v && docker compose up --build -d
```

> ⚠️ Flag `-v` menghapus volume — **data PostgreSQL akan hilang**.

---

### 📋 Cek Status & Log

```bash
# Lihat status semua container
podman ps

# Lihat log real-time API
podman logs -f omni_api

# Lihat log real-time Postgres
podman logs -f omni_postgres

# Hanya 50 baris terakhir
podman logs --tail 50 omni_api
```

---

### 🌐 Akses Setelah Container Jalan

| Service | URL |
|---|---|
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/health |
| **Telegram Bot Info** | http://localhost:8000/api/v1/telegram/info |
| **Chat Endpoint** | http://localhost:8000/api/v1/chat/completions |
| **Complaints Endpoint** | http://localhost:8000/api/v1/complaints |

---

## 🤖 Setup Telegram Bot

1. Buka Telegram → cari **@BotFather**
2. Kirim `/newbot` → ikuti instruksi → salin **token**
3. Isi `TELEGRAM_BOT_TOKEN=<token>` di `.env`
4. Restart API: `podman-compose restart api`
5. Cek bot aktif: `curl http://localhost:8000/api/v1/telegram/info`

**Cari tahu Chat ID kamu** (untuk notifikasi HITL supervisor):
- Kirim pesan ke bot [@userinfobot](https://t.me/userinfobot)
- Salin ID → isi `TELEGRAM_ADMIN_CHAT_ID=<id>` di `.env`

---

## 🔌 Koneksi ke Frontend (OpenAI-Compatible)

Arahkan frontend atau tool apapun ke backend ini:

- **Base URL:** `http://localhost:8000/api/v1`
- **API Key:** isi nilai apapun (dev mode tidak butuh auth)
- **Model:** `omni-resolve-ai`

---

## 🛠️ Testing & Debugging

Gunakan perintah `curl` berikut untuk mengetes sistem Anda secara langsung dari terminal. Semua perintah ini aman karena tidak mengekspos API Key Anda (key diambil otomatis dari `.env` oleh server).

### 1. Cek Diagnostik (LLM, DB, Telegram)
Pastikan semua organ vital sistem tersambung:
```bash
curl -s http://localhost:8000/api/v1/diagnostic | python3 -m json.tool
```

### 2. Kirim Komplain (Full Multi-Agent Pipeline)
Menjalankan alur 4 agen (Liaison → Auditor → Negotiator → Orchestrator).

**Skenario A: Cat Tembok Salah Warna (Barang Murah)**
```bash
curl -X POST http://localhost:8000/api/v1/complaints \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Halo Qhomemart, saya beli Cat Dulux (Order ORD-QHM-003) kok warnanya salah? Pesan putih datang kuning. Saya CUST-002."
  }' | python3 -m json.tool
```

**Skenario B: Sofa Mahal Rusak Kena Hujan (Barang Mahal, HITL Supervisor Trigger)**
```bash
curl -X POST http://localhost:8000/api/v1/complaints \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Sofa pesanan saya hancur dan basah semua pas sampai! Terpal pickup kurirnya bocor katanya. Minta ganti baru sekarang juga! Order ORD-QHM-005, Customer CUST-001."
  }' | python3 -m json.tool
```

### 3. Chat Langsung (OpenAI Compatible)
Tes respon LLM secara langsung (berguna untuk integrasi ke frontend lain).
```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "omni-resolve-ai",
    "messages": [{"role": "user", "content": "Tes koneksi. Siapa namamu?"}]
  }' | python3 -m json.tool
```

---

## 🧪 Unit Testing

Untuk pengujian otomatis yang lebih mendalam:

```bash
# Jalankan semua skenario test (Kasus A & B)
pytest tests/ -v
```

---

## 📁 Struktur Proyek

```
OmniResolve-AI/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.override.yml   ← dev overrides (hot-reload, SELinux :Z)
├── .env.example                  ← template env vars (JANGAN commit .env!)
├── requirements.txt
├── src/
│   ├── config.py                 ← centralized settings (pydantic-settings)
│   ├── agents/
│   │   ├── liaison_agent.py          ← Agent A: Front-End Intelligence
│   │   ├── logistics_auditor.py      ← Agent B: Deep Research + self-correction
│   │   ├── strategic_negotiator.py   ← Agent C: CLV Decision Maker
│   │   └── supply_chain_orchestrator.py ← Agent D: Action Executor
│   ├── graph/
│   │   ├── state.py              ← GraphState TypedDict (shared memory)
│   │   └── workflow.py           ← LangGraph StateGraph builder
│   ├── tools/
│   │   ├── inventory_tools.py    ← mock ERP inventory & customer profile
│   │   ├── courier_tools.py      ← mock courier API
│   │   ├── erp_tools.py          ← mock ERP actions (stock, PO, refund)
│   │   └── vector_store.py       ← pgvector policy document search
│   ├── telegram_bot/
│   │   ├── bot.py                ← entry point (polling / webhook)
│   │   ├── handlers.py           ← message, photo, command handlers
│   │   └── session.py            ← per-customer conversation state
│   └── api/
│       ├── main.py               ← FastAPI app + Telegram lifecycle
│       └── routers/
│           ├── health.py             ← GET /health
│           ├── complaints.py         ← POST /api/v1/complaints
│           ├── chat.py               ← POST /api/v1/chat/completions
│           └── telegram_webhook.py   ← POST /api/v1/telegram/webhook
├── db/
│   ├── init.sql                  ← schema + pgvector setup
│   └── seed.sql                  ← demo data
└── tests/
    └── test_scenarios.py         ← demo scenarios (Kasus A & B)
```

---

## 🚢 Deployment ke SumoPod

1. Push image ke registry:
   ```bash
   podman build -t omniresolve-ai:latest .
   podman push omniresolve-ai:latest docker.io/<username>/omniresolve-ai:latest
   ```

2. Di SumoPod dashboard, set environment variables (sama seperti `.env`)

3. Ubah mode Telegram ke webhook:
   ```env
   TELEGRAM_MODE=webhook
   TELEGRAM_WEBHOOK_URL=https://your-app.sumopod.com
   ```

4. Health check endpoint sudah siap: `GET /health`
