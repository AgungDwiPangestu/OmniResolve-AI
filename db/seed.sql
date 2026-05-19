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
('CUST-999', 'Pelanggan Baru', 'newbie@email.com', '081199998888', 'Bantul, Yogyakarta', FALSE, 0.00, 1, 0),
('CUST-004', 'Agus Setiawan', 'agus.s@email.com', '08122334455', 'Jl. Monjali No. 12, Sleman, Yogyakarta', FALSE, 320000.00, 2, 0),
('CUST-005', 'Rina Wijaya', 'rina.w@email.com', '08778899001', 'Jl. Godean Km 4, Sleman, Yogyakarta', TRUE, 12500000.00, 8, 1),
('CUST-006', 'Dian Sasmita', 'dian.s@email.com', '08215566778', 'Jl. Wates Km 2, Bantul, Yogyakarta', FALSE, 240000.00, 2, 0),
('CUST-007', 'Bambang Triyono', 'bambang.t@email.com', '08139988776', 'Jl. Solo Km 12, Sleman, Yogyakarta', TRUE, 45000000.00, 20, 0),
('CUST-008', 'Lina Marlina', 'lina.m@email.com', '08997766554', 'Jl. Parangtritis Km 6, Bantul, Yogyakarta', FALSE, 3500000.00, 1, 0);

-- -----------------------------------------------------------------------------
-- 2. PRODUCTS (Katalog Qhomemart)
-- -----------------------------------------------------------------------------
INSERT INTO products (product_id, category, product_name, price_idr, stock_available, warehouse_location, warehouse_condition) VALUES
('PRD-001', 'Bahan Bangunan', 'Granit Lantai Niro Granite 60x60 (Dus)', 250000.00, 50, 'Gudang Utama A1', 'good'),
('PRD-002', 'Bahan Bangunan', 'Semen Instan Mortar Utama (MU-380) 40kg', 85000.00, 0, 'Gudang Material B2', 'depleted'),
('PRD-003', 'Furnitur', 'Rak Dinding Minimalis Kayu', 150000.00, 12, 'Gudang Furnitur F1', 'good'),
('PRD-004', 'Sanitary', 'Kloset Duduk Toto Eco Washer Tipe CW421J', 2400000.00, 5, 'Gudang Sanitary D3', 'damaged_in_warehouse'),
('PRD-005', 'Furnitur', 'Sofa Minimalis L-Shape Fabric (Abu-abu)', 5500000.00, 2, 'Gudang Furnitur F1', 'damaged_in_warehouse'),
('PRD-006', 'Cat & Perlengkapan', 'Cat Tembok Dulux Catylac Putih 5kg', 160000.00, 25, 'Gudang Cat C1', 'good'),
('PRD-007', 'Sanitary', 'Keran Air Cabang Stainless', 95000.00, 15, 'Gudang Sanitary D3', 'good'),
('PRD-008', 'Kelistrikan', 'Lampu LED Philips 12W (Pack isi 4)', 120000.00, 30, 'Gudang Listrik E2', 'good'),
('PRD-009', 'Sanitary', 'Water Heater Ariston 15L Tipe Andris2 R', 2250000.00, 8, 'Gudang Sanitary D3', 'good'),
('PRD-010', 'Furnitur', 'Meja Makan Kayu Jati Minimalis', 3500000.00, 3, 'Gudang Furnitur F1', 'good');

-- -----------------------------------------------------------------------------
-- 3. ORDERS
-- -----------------------------------------------------------------------------
INSERT INTO orders (order_id, customer_id, order_date, total_amount_idr, status) VALUES
('ORD-QHM-001', 'CUST-003', NOW() - INTERVAL '5 days', 5000000.00, 'delivered'),
('ORD-QHM-002', 'CUST-999', NOW() - INTERVAL '1 days', 85000.00, 'pending'),
('ORD-QHM-003', 'CUST-002', NOW() - INTERVAL '3 days', 150000.00, 'delivered'),
('ORD-QHM-004', 'CUST-001', NOW() - INTERVAL '4 days', 2400000.00, 'delivered'),
('ORD-QHM-005', 'CUST-001', NOW() - INTERVAL '2 days', 5500000.00, 'delivered'),
('ORD-QHM-006', 'CUST-004', NOW() - INTERVAL '2 days', 320000.00, 'delivered'),
('ORD-QHM-007', 'CUST-005', NOW() - INTERVAL '3 days', 95000.00, 'delivered'),
('ORD-QHM-008', 'CUST-006', NOW() - INTERVAL '4 days', 240000.00, 'delivered'),
('ORD-QHM-009', 'CUST-007', NOW() - INTERVAL '1 days', 2250000.00, 'delivered'),
('ORD-QHM-010', 'CUST-008', NOW() - INTERVAL '3 days', 3500000.00, 'delivered');

-- -----------------------------------------------------------------------------
-- 4. ORDER ITEMS
-- -----------------------------------------------------------------------------
INSERT INTO order_items (order_id, product_id, quantity, subtotal_idr) VALUES
('ORD-QHM-001', 'PRD-001', 20, 5000000.00),
('ORD-QHM-002', 'PRD-002', 1, 85000.00),
('ORD-QHM-003', 'PRD-003', 1, 150000.00),
('ORD-QHM-004', 'PRD-004', 1, 2400000.00),
('ORD-QHM-005', 'PRD-005', 1, 5500000.00),
('ORD-QHM-006', 'PRD-006', 2, 320000.00),
('ORD-QHM-007', 'PRD-007', 1, 95000.00),
('ORD-QHM-008', 'PRD-008', 2, 240000.00),
('ORD-QHM-009', 'PRD-009', 1, 2250000.00),
('ORD-QHM-010', 'PRD-010', 1, 3500000.00);

-- -----------------------------------------------------------------------------
-- 5. DELIVERIES (Logistik Kurir / Armada)
-- -----------------------------------------------------------------------------
INSERT INTO deliveries (tracking_id, order_id, courier_name, status, condition_on_pickup, damage_reported_by_courier, delivery_logs) VALUES
(
    'QHM-DEL-0011234', 'ORD-QHM-001', 'Armada Qhomemart', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-14 08:00", "status": "Barang dimuat ke armada internal", "location": "Yogyakarta"},
        {"time": "2026-05-14 11:30", "status": "Terkirim — guncangan keras di jalan berlubang, tumpukan granit retak", "location": "Sleman"}
    ]'::jsonb
),
(
    'QHM-DEL-8821345', 'ORD-QHM-003', 'Armada Qhomemart', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-12 08:00", "status": "Barang diambil dari Gudang Qhomemart Jogja", "location": "Yogyakarta"},
        {"time": "2026-05-12 10:30", "status": "Dalam perjalanan — tergelincir guncangan parah", "location": "Sleman"},
        {"time": "2026-05-12 16:45", "status": "Terkirim — terdeteksi benturan parah pada packing kayu", "location": "Sleman"}
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
),
(
    'QHM-DEL-0061234', 'ORD-QHM-006', 'Armada Qhomemart', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-17 08:00", "status": "Barang diambil dari Gudang Cat", "location": "Yogyakarta"},
        {"time": "2026-05-17 11:15", "status": "Terkirim — kaleng penyok dan rembes cat keluar", "location": "Sleman"}
    ]'::jsonb
),
(
    'JNT-7721345', 'ORD-QHM-007', 'J&T Express', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-16 09:00", "status": "Paket masuk drop point J&T", "location": "Yogyakarta"},
        {"time": "2026-05-17 14:30", "status": "Terkirim — pecah sebagian", "location": "Sleman"}
    ]'::jsonb
),
(
    'SCE-8812341', 'ORD-QHM-008', 'SiCepat', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-15 10:00", "status": "Paket diserahkan ke kurir", "location": "Yogyakarta"},
        {"time": "2026-05-15 16:30", "status": "Diterima — box penyok basah terkena benturan cargo", "location": "Bantul"}
    ]'::jsonb
),
(
    'JNE-9902341', 'ORD-QHM-009', 'JNE Trucking', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-18 08:30", "status": "Barang diserahkan ke cargo", "location": "Yogyakarta"},
        {"time": "2026-05-18 17:45", "status": "Terkirim — casing retak retak", "location": "Sleman"}
    ]'::jsonb
),
(
    'QHM-DEL-010331', 'ORD-QHM-010', 'Armada Qhomemart', 'delivered', 'intact', FALSE,
    '[
        {"time": "2026-05-16 09:00", "status": "Meja dimuat ke armada internal", "location": "Yogyakarta"},
        {"time": "2026-05-16 12:00", "status": "Tiba di lokasi penerima", "location": "Bantul"}
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
