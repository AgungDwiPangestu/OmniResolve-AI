#  OmniResolve-AI

**Autonomous Omni-Channel Retail Concierge & Conflict Resolver**

Sistem Multi-Agent berbasis **ReAct (Reason + Act)** + **LangGraph** untuk automasi resolusi konflik pelanggan dan optimalisasi inventaris real-time di industri ritel.

---

## 🏗 Arsitektur

```
Pelanggan
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
| **OpenAI-Compatible API** | Backend compatible dengan claude-office dan frontend manapun |

## ⚙️ Tech Stack

| Layer | Teknologi |
|---|---|
| **Orchestration** | LangGraph (Stateful Multi-Agent) |
| **LLM** | SumoPod API Marketplace (Anthropic Claude / GLM — OpenAI-compatible) |
| **Vector DB** | pgvector (PostgreSQL extension) |
| **Database** | PostgreSQL 16 |
| **API** | FastAPI + Swagger |
| **Container** | Docker / Podman (kompatibel) |
| **Deployment** | SumoPod |

## 🚀 Quick Start

### Prerequisites
- Podman atau Docker
- `podman-compose` atau `docker compose`

### 1. Clone & Setup

```bash
git clone https://github.com/username/OmniResolve-AI.git
cd OmniResolve-AI
cp .env.example .env
# Edit .env — isi LLM_API_KEY dengan SumoPod API key kamu
```

### 2. Jalankan (Podman)

```bash
podman-compose up --build
```

### 3. Jalankan (Docker)

```bash
docker compose up --build
```

### 4. Akses

| Service | URL |
|---|---|
| API Docs (Swagger) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| Chat Endpoint | http://localhost:8000/api/v1/chat/completions |

## 🔌 Koneksi ke claude-office

Setelah backend berjalan, arahkan claude-office ke:
- **Base URL:** `http://localhost:8000/api/v1`
- **API Key:** isi nilai apapun (dev mode tidak butuh auth)
- **Model:** `omni-resolve-ai`

## 🧪 Demo Scenarios

```bash
# Jalankan semua test
pytest tests/ -v

# Test via curl — Kasus A (pelanggan baru)
curl -X POST http://localhost:8000/api/v1/complaints \
  -H "Content-Type: application/json" \
  -d '{"message": "Rak dinding saya warnanya salah. Order ORD-003. Customer CUST-002."}'

# Test via curl — Kasus B (pelanggan setia, barang rusak)
curl -X POST http://localhost:8000/api/v1/complaints \
  -H "Content-Type: application/json" \
  -d '{"message": "Sofa saya rusak parah waktu diterima! Order ORD-004, Customer CUST-001."}'
```

## 📁 Struktur Proyek

```
OmniResolve-AI/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.override.yml   ← dev overrides (hot-reload)
├── .env.example                  ← template env vars
├── requirements.txt
├── src/
│   ├── config.py                 ← centralized settings
│   ├── agents/
│   │   ├── liaison_agent.py          ← Agent A
│   │   ├── logistics_auditor.py      ← Agent B
│   │   ├── strategic_negotiator.py   ← Agent C
│   │   └── supply_chain_orchestrator.py ← Agent D
│   ├── graph/
│   │   ├── state.py              ← GraphState TypedDict
│   │   └── workflow.py           ← LangGraph StateGraph
│   ├── tools/
│   │   ├── inventory_tools.py    ← mock ERP inventory
│   │   ├── courier_tools.py      ← mock courier API
│   │   ├── erp_tools.py          ← mock ERP actions
│   │   └── vector_store.py       ← pgvector policy search
│   └── api/
│       ├── main.py               ← FastAPI app
│       └── routers/
│           ├── health.py         ← GET /health
│           ├── complaints.py     ← POST /api/v1/complaints
│           └── chat.py           ← POST /api/v1/chat/completions
├── db/
│   ├── init.sql                  ← schema + pgvector setup
│   └── seed.sql                  ← demo data
└── tests/
    └── test_scenarios.py         ← demo scenarios
```
