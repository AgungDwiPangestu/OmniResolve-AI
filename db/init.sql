-- =============================================================================
-- db/init.sql — PostgreSQL Database Initialization
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- 1. ERP & CRM TABLES (Data Dummy Qhomemart)
-- =============================================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(100) PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    is_loyal BOOLEAN DEFAULT FALSE,
    lifetime_value_idr DECIMAL(15, 2) DEFAULT 0,
    total_orders INT DEFAULT 0,
    previous_complaints INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(100) PRIMARY KEY,
    category VARCHAR(100),
    product_name VARCHAR(255) NOT NULL,
    price_idr DECIMAL(15, 2) NOT NULL,
    stock_available INT DEFAULT 0,
    warehouse_location VARCHAR(100),
    warehouse_condition VARCHAR(50) DEFAULT 'good',
    last_physical_check DATE
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id            SERIAL PRIMARY KEY,
    product_id    VARCHAR(100) REFERENCES products(product_id),
    movement_type VARCHAR(20) NOT NULL, -- 'in' | 'out' | 'reserve' | 'write_off'
    quantity      INT NOT NULL,
    reason        VARCHAR(200),         -- 'initial_stock', 'po_received', 'replacement', 'refund', 'write_off', 'damage_adjustment'
    order_id      VARCHAR(100),
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_created ON stock_movements(created_at DESC);

CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(100) PRIMARY KEY,
    customer_id VARCHAR(100) REFERENCES customers(customer_id),
    order_date TIMESTAMPTZ DEFAULT NOW(),
    total_amount_idr DECIMAL(15, 2),
    status VARCHAR(50) DEFAULT 'pending' -- pending, paid, shipped, delivered, cancelled
);

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id VARCHAR(100) REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id VARCHAR(100) REFERENCES products(product_id),
    quantity INT NOT NULL,
    subtotal_idr DECIMAL(15, 2)
);

CREATE TABLE IF NOT EXISTS deliveries (
    tracking_id VARCHAR(100) PRIMARY KEY,
    order_id VARCHAR(100) REFERENCES orders(order_id),
    courier_name VARCHAR(100), -- JNT, JNE, Qhomemart Fleet
    status VARCHAR(50), -- on_process, on_delivery, delivered, delivered_with_damage
    last_update TIMESTAMPTZ DEFAULT NOW(),
    condition_on_pickup VARCHAR(50),
    damage_reported_by_courier BOOLEAN DEFAULT FALSE,
    delivery_logs JSONB -- Array of events
);

-- =============================================================================
-- 2. SYSTEM TABLES (Audit Trail & Vector)
-- =============================================================================

CREATE TABLE IF NOT EXISTS complaint_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    raw_input TEXT NOT NULL,
    customer_id VARCHAR(100),
    order_id VARCHAR(100),
    complaint_type VARCHAR(50),
    sentiment_score DECIMAL(3, 2),
    claim_valid BOOLEAN,
    stock_status VARCHAR(50),
    audit_notes TEXT,
    decision_type VARCHAR(50),
    compensation_value_idr DECIMAL(15, 2),
    requires_human_approval BOOLEAN DEFAULT FALSE,
    chain_of_thought TEXT,
    actions_taken JSONB,
    actions_failed JSONB,
    final_response TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'completed'
);

CREATE TABLE IF NOT EXISTS langchain_pg_collection (
    uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR NOT NULL,
    cmetadata JSONB
);

CREATE TABLE IF NOT EXISTS langchain_pg_embedding (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID REFERENCES langchain_pg_collection(uuid) ON DELETE CASCADE,
    embedding vector(1536),
    document TEXT,
    cmetadata JSONB,
    custom_id VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_embedding_vector
    ON langchain_pg_embedding USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

-- Trigger for updated_at
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
