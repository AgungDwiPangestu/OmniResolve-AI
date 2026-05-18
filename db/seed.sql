-- =============================================================================
-- db/seed.sql — Qhomemart Dummy Data
-- =============================================================================

-- Hapus data lama agar aman jika dijalankan berulang
TRUNCATE TABLE deliveries CASCADE;
TRUNCATE TABLE order_items CASCADE;
TRUNCATE TABLE orders CASCADE;
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE customers CASCADE;

-- -----------------------------------------------------------------------------
-- 1. CUSTOMERS
-- -----------------------------------------------------------------------------
INSERT INTO customers (customer_id, customer_name, email, phone, address, is_loyal, lifetime_value_idr, total_orders, previous_complaints) VALUES
('CUST-001', 'Budi Hartono', 'budi.h@email.com', '081234567890', 'Jl. Kaliurang Km 7, Sleman, Yogyakarta', TRUE, 25000000.00, 12, 1),
('CUST-002', 'Sari Dewi', 'saridewi99@email.com', '085712345678', 'Jl. Gejayan No. 45, Yogyakarta', FALSE, 1850000.00, 2, 0),
('CUST-003', 'Kontraktor Jaya Abadi', 'purchasing@jayaabadi.co.id', '0274555666', 'Jl. Magelang Km 10, Sleman', TRUE, 150000000.00, 45, 2),
('CUST-999', 'Pelanggan Baru', 'newbie@email.com', '081199998888', 'Bantul, Yogyakarta', FALSE, 0.00, 1, 0);

-- -----------------------------------------------------------------------------
-- 2. PRODUCTS (Katalog Qhomemart)
-- -----------------------------------------------------------------------------
INSERT INTO products (product_id, category, product_name, price_idr, stock_available, warehouse_location, warehouse_condition) VALUES
('PRD-001', 'Bahan Bangunan', 'Granit Lantai Niro Granite 60x60 (Dus)', 250000.00, 50, 'Gudang Utama A1', 'good'),
('PRD-002', 'Bahan Bangunan', 'Semen Instan Mortar Utama (MU-380) 40kg', 85000.00, 0, 'Gudang Material B2', 'depleted'),
('PRD-003', 'Furnitur', 'Rak Dinding Minimalis Kayu', 150000.00, 12, 'Gudang Furnitur F1', 'good'),
('PRD-004', 'Sanitary', 'Kloset Duduk Toto Eco Washer Tipe CW421J', 2400000.00, 5, 'Gudang Sanitary D3', 'damaged_in_warehouse'),
('PRD-005', 'Furnitur', 'Sofa Minimalis L-Shape Fabric (Abu-abu)', 5500000.00, 2, 'Gudang Furnitur F1', 'damaged_in_warehouse');

-- -----------------------------------------------------------------------------
-- 3. ORDERS
-- -----------------------------------------------------------------------------
INSERT INTO orders (order_id, customer_id, order_date, total_amount_idr, status) VALUES
('ORD-QHM-001', 'CUST-003', NOW() - INTERVAL '5 days', 5000000.00, 'delivered'),
('ORD-QHM-002', 'CUST-999', NOW() - INTERVAL '1 days', 85000.00, 'pending'),
('ORD-QHM-003', 'CUST-002', NOW() - INTERVAL '3 days', 150000.00, 'delivered'),
('ORD-QHM-004', 'CUST-001', NOW() - INTERVAL '4 days', 2400000.00, 'delivered'),
('ORD-QHM-005', 'CUST-001', NOW() - INTERVAL '2 days', 5500000.00, 'delivered');

-- -----------------------------------------------------------------------------
-- 4. ORDER ITEMS
-- -----------------------------------------------------------------------------
INSERT INTO order_items (order_id, product_id, quantity, subtotal_idr) VALUES
('ORD-QHM-001', 'PRD-001', 20, 5000000.00),
('ORD-QHM-002', 'PRD-002', 1, 85000.00),
('ORD-QHM-003', 'PRD-003', 1, 150000.00),
('ORD-QHM-004', 'PRD-004', 1, 2400000.00),
('ORD-QHM-005', 'PRD-005', 1, 5500000.00);

-- -----------------------------------------------------------------------------
-- 5. DELIVERIES (Logistik Kurir / Armada)
-- -----------------------------------------------------------------------------
INSERT INTO deliveries (tracking_id, order_id, courier_name, status, condition_on_pickup, damage_reported_by_courier, delivery_logs) VALUES
(
    'QHM-DEL-8821345', 'ORD-QHM-003', 'Armada Qhomemart', 'delivered', 'intact', FALSE,
    '[
        {"time": "2026-05-12 08:00", "status": "Barang diambil dari Gudang Qhomemart Jogja", "location": "Yogyakarta"},
        {"time": "2026-05-12 10:30", "status": "Dalam perjalanan (Armada Internal)", "location": "Sleman"},
        {"time": "2026-05-12 16:45", "status": "Terkirim — diterima oleh: Bpk. Supri", "location": "Sleman"}
    ]'::jsonb
),
(
    'CARGO-5590234', 'ORD-QHM-004', 'Dakota Cargo', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-09 09:00", "status": "Paket diambil dari Gudang Qhomemart", "location": "Yogyakarta"},
        {"time": "2026-05-10 20:15", "status": "Hub transit kargo — indikasi benturan ringan", "location": "Semarang"},
        {"time": "2026-05-11 14:20", "status": "Terkirim — ada laporan packing kayu sedikit rusak", "location": "Magelang"}
    ]'::jsonb
),
(
    'QHM-DEL-9993331', 'ORD-QHM-005', 'Armada Qhomemart', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-13 08:00", "status": "Barang dimuat ke pickup Qhomemart", "location": "Yogyakarta"},
        {"time": "2026-05-13 09:30", "status": "Terkena hujan lebat di perjalanan, terpal bocor", "location": "Bantul"},
        {"time": "2026-05-13 10:00", "status": "Terkirim — catatan: basah/kotor", "location": "Bantul"}
    ]'::jsonb
);

-- -----------------------------------------------------------------------------
-- 6. COMPLAINT SESSIONS (Histori Komplain Demo)
-- -----------------------------------------------------------------------------
INSERT INTO complaint_sessions (
    session_id, raw_input, customer_id, order_id, complaint_type,
    sentiment_score, claim_valid, stock_status, decision_type,
    compensation_value_idr, requires_human_approval, chain_of_thought,
    final_response, status
) VALUES
(
    'demo-session-qhm-003',
    'Halo Qhomemart, saya beli Cat Dulux (Order ORD-QHM-003) kok warnanya salah? Pesan putih datang kuning. Saya CUST-002.',
    'CUST-002', 'ORD-QHM-003', 'wrong_item', -0.45, TRUE, 'available', 'voucher', 75000, FALSE,
    'Reasoning: Pelanggan (CLV Rp 1.8jt). Barang salah warna dari pihak gudang. Kurir aman. Berikan voucher kompensasi agar pelanggan bisa beli lagi.',
    'Halo Kak Sari Dewi, mohon maaf atas kesalahan warna cat. Kami berikan voucher Rp 75.000 untuk Anda.',
    'completed'
),
(
    'demo-session-qhm-005',
    'Sofa pesanan saya hancur dan basah semua pas sampai! Terpal pickup kurirnya bocor katanya. Order ORD-QHM-005, Customer CUST-001.',
    'CUST-001', 'ORD-QHM-005', 'damaged_item', -0.95, TRUE, 'damaged_in_warehouse', 'replacement', 0, TRUE,
    'Reasoning: Pelanggan prioritas (CLV Rp 25jt). Barang mahal (Rp 5.5jt). Bukti logistik menunjukkan bocor hujan. Action: Replacement. Butuh Approval Manager karena > Rp 1jt.',
    'Yth Bapak Budi, kami mohon maaf sebesar-besarnya. Sofa Anda akan kami tarik dan ganti baru. Kasus ini sedang dalam review Manager kami.',
    'pending_hitl'
)
ON CONFLICT (session_id) DO NOTHING;
