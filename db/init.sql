-- =============================================================================
-- db/init.sql — PostgreSQL Database Initialization
-- Dijalankan otomatis oleh Docker entrypoint saat container pertama kali start
-- =============================================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- Table: complaint_sessions
-- Menyimpan semua sesi keluhan dan hasilnya untuk audit trail
-- =============================================================================
CREATE TABLE IF NOT EXISTS complaint_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      VARCHAR(100) UNIQUE NOT NULL,
    raw_input       TEXT NOT NULL,
    customer_id     VARCHAR(100),
    order_id        VARCHAR(100),
    complaint_type  VARCHAR(50),
    sentiment_score DECIMAL(3, 2),

    -- Hasil audit
    claim_valid     BOOLEAN,
    stock_status    VARCHAR(50),
    audit_notes     TEXT,

    -- Keputusan
    decision_type           VARCHAR(50),
    compensation_value_idr  DECIMAL(15, 2),
    requires_human_approval BOOLEAN DEFAULT FALSE,
    chain_of_thought        TEXT,

    -- Aksi
    actions_taken   JSONB,
    actions_failed  JSONB,

    -- Response
    final_response  TEXT,

    -- Metadata
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    status          VARCHAR(20) DEFAULT 'completed'  -- 'pending_hitl' | 'completed' | 'error'
);

-- Index untuk query cepat
CREATE INDEX IF NOT EXISTS idx_sessions_customer_id ON complaint_sessions(customer_id);
CREATE INDEX IF NOT EXISTS idx_sessions_order_id ON complaint_sessions(order_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON complaint_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON complaint_sessions(status);

-- =============================================================================
-- Table: policy_documents (pgvector)
-- Dokumen kebijakan yang di-embed untuk semantic search
-- =============================================================================
CREATE TABLE IF NOT EXISTS langchain_pg_collection (
    uuid   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name   VARCHAR NOT NULL,
    cmetadata JSONB
);

CREATE TABLE IF NOT EXISTS langchain_pg_embedding (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID REFERENCES langchain_pg_collection(uuid) ON DELETE CASCADE,
    embedding   vector(1536),   -- Dimensi untuk text-embedding-3-small
    document    TEXT,
    cmetadata   JSONB,
    custom_id   VARCHAR
);

-- IVFFlat index untuk approximate nearest neighbor search
-- Catatan: Butuh minimal 100 rows sebelum index ini efektif
CREATE INDEX IF NOT EXISTS idx_embedding_vector
    ON langchain_pg_embedding USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

-- =============================================================================
-- Function: updated_at auto-update trigger
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sessions_updated_at
    BEFORE UPDATE ON complaint_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
