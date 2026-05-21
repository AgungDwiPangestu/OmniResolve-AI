-- =============================================================================
-- db/seed.sql — Comprehensive Qhomemart Dummy Data (30 Mapped Sandboxes)
-- =============================================================================

-- Hapus data lama agar aman jika dijalankan berulang
TRUNCATE TABLE deliveries CASCADE;
TRUNCATE TABLE order_items CASCADE;
TRUNCATE TABLE orders CASCADE;
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE customers CASCADE;

-- -----------------------------------------------------------------------------
-- 1. CUSTOMERS (CUST-001 s/d CUST-030)
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
('CUST-008', 'Lina Marlina', 'lina.m@email.com', '08997766554', 'Jl. Parangtritis Km 6, Bantul, Yogyakarta', FALSE, 3500000.00, 1, 0),
('CUST-009', 'Hendra Wijaya', 'hendra.w@email.com', '08123459999', 'Jl. Ringroad Utara No. 12, Depok, Sleman, Yogyakarta', FALSE, 180000.00, 1, 0),
('CUST-010', 'Dewi Lestari', 'dewi.l@email.com', '0819998877', 'Jl. Kusumanegara No. 88, Umbulharjo, Yogyakarta', TRUE, 195000.00, 1, 0),
('CUST-011', 'Andi Pratama', 'andi.pratama@email.com', '081211112222', 'Jl. Affandi No. 10, Sleman, Yogyakarta', TRUE, 8500000.00, 5, 0),
('CUST-012', 'Siti Aminah', 'siti.aminah@email.com', '081322223333', 'Jl. Malioboro No. 25, Yogyakarta', FALSE, 680000.00, 2, 1),
('CUST-013', 'Joko Susilo', 'joko.s@email.com', '081433334444', 'Jl. Gajah Mada No. 15, Danurejan, Yogyakarta', FALSE, 250000.00, 1, 0),
('CUST-014', 'Eka Rahmawati', 'eka.rahma@email.com', '081544445555', 'Jl. Katamso No. 40, Mergangsan, Yogyakarta', TRUE, 12000000.00, 7, 0),
('CUST-015', 'Fajar Nugroho', 'fajar.nugroho@email.com', '081655556666', 'Jl. Kusumanegara No. 5, Yogyakarta', FALSE, 120000.00, 1, 0),
('CUST-016', 'Gita Permata', 'gita.p@email.com', '081766667777', 'Jl. Jenderal Sudirman No. 50, Yogyakarta', TRUE, 1850000.00, 3, 0),
('CUST-017', 'Hadi Syahputra', 'hadi.s@email.com', '081877778888', 'Jl. Imogiri Timur Km 5, Bantul, Yogyakarta', FALSE, 3200000.00, 4, 1),
('CUST-018', 'Indah Lestari', 'indah.l@email.com', '081988889999', 'Jl. Wonosari Km 6, Banguntapan, Bantul', TRUE, 15000000.00, 10, 0),
('CUST-019', 'Kurniawan Dwi', 'kurniawan.d@email.com', '082199990000', 'Jl. Palagan No. 99, Ngaglik, Sleman', FALSE, 75000.00, 1, 0),
('CUST-020', 'Lilis Suryani', 'lilis.s@email.com', '082211223344', 'Jl. Kaliurang Km 10, Ngaglik, Sleman', FALSE, 650000.00, 2, 0),
('CUST-021', 'Mega Utami', 'mega.utami@email.com', '082322334455', 'Jl. Kabupaten No. 8, Sleman, Yogyakarta', TRUE, 5400000.00, 6, 0),
('CUST-022', 'Novianto Eko', 'novianto.eko@email.com', '082433445566', 'Jl. Magelang Km 6, Sleman, Yogyakarta', FALSE, 85000.00, 1, 0),
('CUST-023', 'Oki Setiawan', 'oki.setiawan@email.com', '082544556677', 'Jl. Godean Km 7, Sleman, Yogyakarta', FALSE, 35000.00, 1, 0),
('CUST-024', 'Putri Handayani', 'putri.h@email.com', '082655667788', 'Jl. Bantul Km 4, Dongkelan, Bantul', TRUE, 2200000.00, 3, 0),
('CUST-025', 'Rian Hidayat', 'rian.h@email.com', '082766778899', 'Jl. Parangtritis Km 4, Sewon, Bantul', FALSE, 195000.00, 1, 0),
('CUST-026', 'Siska Amelia', 'siska.a@email.com', '082877889900', 'Jl. Tamansiswa No. 120, Yogyakarta', TRUE, 420000.00, 2, 0),
('CUST-027', 'Taufik Hidayat', 'taufik.h@email.com', '082988990011', 'Jl. HOS Cokroaminoto No. 30, Yogyakarta', FALSE, 60000.00, 1, 0),
('CUST-028', 'Utami Ningsih', 'utami.n@email.com', '083199001122', 'Jl. Tajem Km 2, Maguwoharjo, Sleman', TRUE, 110000.00, 1, 0),
('CUST-029', 'Vicky Prasetyo', 'vicky.p@email.com', '083211223344', 'Jl. Glagahsari No. 15, Umbulharjo, Yogyakarta', FALSE, 55000.00, 1, 0),
('CUST-030', 'Wulan Dari', 'wulan.dari@email.com', '083322334455', 'Jl. C. Simanjuntak No. 10, Terban, Yogyakarta', TRUE, 180000.00, 5, 0);

-- -----------------------------------------------------------------------------
-- 2. PRODUCTS (Katalog Lengkap PRD-001 s/d PRD-030)
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
('PRD-010', 'Furnitur', 'Meja Makan Kayu Jati Minimalis', 3500000.00, 3, 'Gudang Furnitur F1', 'good'),
('PRD-011', 'Kelistrikan', 'Kabel Roll Panasonic 10 Meter', 180000.00, 20, 'Gudang Listrik E2', 'good'),
('PRD-012', 'Bahan Bangunan', 'Semen Tiga Roda 40kg', 65000.00, 50, 'Gudang Material B2', 'good'),
('PRD-013', 'Tools', 'Bor Listrik Bosch GSB 550', 680000.00, 10, 'Gudang Perkakas G1', 'good'),
('PRD-014', 'Peralatan Rumah Tangga', 'Kipas Angin Stand Miyako', 250000.00, 18, 'Gudang Elektronik H2', 'good'),
('PRD-015', 'Dekorasi', 'Cermin Dinding Hexagonal (Set isi 6)', 120000.00, 40, 'Gudang Dekorasi J3', 'good'),
('PRD-016', 'Dapur', 'Kitchen Sink Blanco Stainless', 1850000.00, 4, 'Gudang Sanitary D3', 'good'),
('PRD-017', 'Sanitary', 'Shower Column Set Toto', 3200000.00, 5, 'Gudang Sanitary D3', 'good'),
('PRD-018', 'Cat & Perlengkapan', 'Kuas Cat Nippon Paint 3 Inch', 150000.00, 100, 'Gudang Cat C1', 'good'),
('PRD-019', 'Cat & Perlengkapan', 'Cat Kayu & Besi FTALIT 1kg', 75000.00, 30, 'Gudang Cat C1', 'good'),
('PRD-020', 'Peralatan Rumah Tangga', 'Blender Philips HR2115', 650000.00, 12, 'Gudang Elektronik H2', 'good'),
('PRD-021', 'Tools', 'Obeng Set Kenmaster 31 in 1', 45000.00, 50, 'Gudang Perkakas G1', 'good'),
('PRD-022', 'Kelistrikan', 'Stop Kontak Broco 4 Lubang', 85000.00, 60, 'Gudang Listrik E2', 'good'),
('PRD-023', 'Dekorasi', 'Wallpaper Dinding 3D Foam (Roll)', 35000.00, 80, 'Gudang Dekorasi J3', 'good'),
('PRD-024', 'Furnitur', 'Lemari Pakaian Plastik Club 4 Susun', 280000.00, 15, 'Gudang Furnitur F1', 'good'),
('PRD-025', 'Sanitary', 'Jet Shower Closet Toto', 195000.00, 22, 'Gudang Sanitary D3', 'good'),
('PRD-026', 'Dapur', 'Kompor Gas Rinnai 2 Tungku', 420000.00, 14, 'Gudang Dapur K1', 'good'),
('PRD-027', 'Lantai', 'Keramik Lantai Mulia 40x40 (Dus)', 60000.00, 100, 'Gudang Utama A1', 'good'),
('PRD-028', 'Taman', 'Selang Air Anti Tekuk 15 Meter', 110000.00, 25, 'Gudang Taman L2', 'good'),
('PRD-029', 'Tools', 'Tang Kombinasi Tekiro 7 Inch', 55000.00, 35, 'Gudang Perkakas G1', 'good'),
('PRD-030', 'Kelistrikan', 'Saklar Lampu Panasonic Single', 18000.00, 150, 'Gudang Listrik E2', 'good');

-- -----------------------------------------------------------------------------
-- 3. ORDERS (ORD-QHM-001 s/d ORD-QHM-030)
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
('ORD-QHM-010', 'CUST-008', NOW() - INTERVAL '3 days', 3500000.00, 'delivered'),
('ORD-QHM-011', 'CUST-009', NOW() - INTERVAL '1 days', 180000.00, 'delivered'),
('ORD-QHM-012', 'CUST-010', NOW() - INTERVAL '2 days', 195000.00, 'delivered'),
('ORD-QHM-013', 'CUST-011', NOW() - INTERVAL '4 days', 680000.00, 'delivered'),
('ORD-QHM-014', 'CUST-012', NOW() - INTERVAL '2 days', 250000.00, 'delivered'),
('ORD-QHM-015', 'CUST-013', NOW() - INTERVAL '3 days', 120000.00, 'delivered'),
('ORD-QHM-016', 'CUST-014', NOW() - INTERVAL '5 days', 1850000.00, 'delivered'),
('ORD-QHM-017', 'CUST-015', NOW() - INTERVAL '1 days', 3200000.00, 'delivered'),
('ORD-QHM-018', 'CUST-016', NOW() - INTERVAL '3 days', 150000.00, 'delivered'),
('ORD-QHM-019', 'CUST-017', NOW() - INTERVAL '4 days', 75000.00, 'delivered'),
('ORD-QHM-020', 'CUST-018', NOW() - INTERVAL '2 days', 650000.00, 'delivered'),
('ORD-QHM-021', 'CUST-019', NOW() - INTERVAL '5 days', 45000.00, 'delivered'),
('ORD-QHM-022', 'CUST-020', NOW() - INTERVAL '1 days', 85000.00, 'delivered'),
('ORD-QHM-023', 'CUST-021', NOW() - INTERVAL '3 days', 35000.00, 'delivered'),
('ORD-QHM-024', 'CUST-022', NOW() - INTERVAL '2 days', 280000.00, 'delivered'),
('ORD-QHM-025', 'CUST-023', NOW() - INTERVAL '4 days', 195000.00, 'delivered'),
('ORD-QHM-026', 'CUST-024', NOW() - INTERVAL '1 days', 420000.00, 'delivered'),
('ORD-QHM-027', 'CUST-025', NOW() - INTERVAL '3 days', 60000.00, 'delivered'),
('ORD-QHM-028', 'CUST-026', NOW() - INTERVAL '4 days', 110000.00, 'delivered'),
('ORD-QHM-029', 'CUST-027', NOW() - INTERVAL '2 days', 55000.00, 'delivered'),
('ORD-QHM-030', 'CUST-028', NOW() - INTERVAL '3 days', 18000.00, 'delivered');

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
('ORD-QHM-010', 'PRD-010', 1, 3500000.00),
('ORD-QHM-011', 'PRD-011', 1, 180000.00),
('ORD-QHM-012', 'PRD-012', 3, 195000.00),
('ORD-QHM-013', 'PRD-013', 1, 680000.00),
('ORD-QHM-014', 'PRD-014', 1, 250000.00),
('ORD-QHM-015', 'PRD-015', 1, 120000.00),
('ORD-QHM-016', 'PRD-016', 1, 1850000.00),
('ORD-QHM-017', 'PRD-017', 1, 3200000.00),
('ORD-QHM-018', 'PRD-018', 1, 150000.00),
('ORD-QHM-019', 'PRD-019', 1, 75000.00),
('ORD-QHM-020', 'PRD-020', 1, 650000.00),
('ORD-QHM-021', 'PRD-021', 1, 45000.00),
('ORD-QHM-022', 'PRD-022', 1, 85000.00),
('ORD-QHM-023', 'PRD-023', 1, 35000.00),
('ORD-QHM-024', 'PRD-024', 1, 280000.00),
('ORD-QHM-025', 'PRD-025', 1, 195000.00),
('ORD-QHM-026', 'PRD-026', 1, 420000.00),
('ORD-QHM-027', 'PRD-027', 1, 60000.00),
('ORD-QHM-028', 'PRD-028', 1, 110000.00),
('ORD-QHM-029', 'PRD-029', 1, 55000.00),
('ORD-QHM-030', 'PRD-030', 1, 18000.00);

-- -----------------------------------------------------------------------------
-- 5. DELIVERIES (Logistik Kurir / Mapped Sandboxes)
-- -----------------------------------------------------------------------------
INSERT INTO deliveries (tracking_id, order_id, courier_name, status, condition_on_pickup, damage_reported_by_courier, delivery_logs) VALUES
-- 1. Valid Damage (Granit)
(
    'QHM-DEL-0011234', 'ORD-QHM-001', 'Armada Qhomemart', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-14 08:00", "status": "Barang dimuat ke armada internal", "location": "Yogyakarta"},
        {"time": "2026-05-14 11:30", "status": "Terkirim — guncangan keras di jalan berlubang, tumpukan granit retak", "location": "Sleman"}
    ]'::jsonb
),
-- 2. Pending (Stock-Out Semen Instan)
(
    'QHM-DEL-0022234', 'ORD-QHM-002', 'Armada Qhomemart', 'pending', 'intact', FALSE,
    '[
        {"time": "2026-05-20 08:00", "status": "Ditunda — menunggu restock pabrik", "location": "Gudang B2"}
    ]'::jsonb
),
-- 3. Valid Damage (Rak Kayu)
(
    'QHM-DEL-8821345', 'ORD-QHM-003', 'Armada Qhomemart', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-12 08:00", "status": "Barang diambil dari Gudang Qhomemart Jogja", "location": "Yogyakarta"},
        {"time": "2026-05-12 10:30", "status": "Dalam perjalanan — tergelincir guncangan parah", "location": "Sleman"},
        {"time": "2026-05-12 16:45", "status": "Terkirim — terdeteksi benturan parah pada packing kayu", "location": "Sleman"}
    ]'::jsonb
),
-- 4. Valid Damage (Kloset Toto)
(
    'CARGO-5590234', 'ORD-QHM-004', 'Dakota Cargo', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-09 09:00", "status": "Paket diambil dari Gudang Qhomemart", "location": "Yogyakarta"},
        {"time": "2026-05-10 20:15", "status": "Hub transit kargo — indikasi benturan ringan", "location": "Semarang"},
        {"time": "2026-05-11 14:20", "status": "Terkirim — ada laporan packing kayu sedikit rusak", "location": "Magelang"}
    ]'::jsonb
),
-- 5. Valid Damage (Sofa L-Shape)
(
    'QHM-DEL-9993331', 'ORD-QHM-005', 'Armada Qhomemart', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-13 08:00", "status": "Barang dimuat ke pickup Qhomemart", "location": "Yogyakarta"},
        {"time": "2026-05-13 09:30", "status": "Terkena hujan lebat di perjalanan, terpal bocor", "location": "Bantul"},
        {"time": "2026-05-13 10:00", "status": "Terkirim — catatan: basah/kotor", "location": "Bantul"}
    ]'::jsonb
),
-- 6. Valid Damage (Cat Tembok)
(
    'QHM-DEL-0061234', 'ORD-QHM-006', 'Armada Qhomemart', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-17 08:00", "status": "Barang diambil dari Gudang Cat", "location": "Yogyakarta"},
        {"time": "2026-05-17 11:15", "status": "Terkirim — kaleng penyok dan rembes cat keluar", "location": "Sleman"}
    ]'::jsonb
),
-- 7. Valid Damage (Keran Air Cabang)
(
    'JNT-7721345', 'ORD-QHM-007', 'J&T Express', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-16 09:00", "status": "Paket masuk drop point J&T", "location": "Yogyakarta"},
        {"time": "2026-05-17 14:30", "status": "Terkirim — pecah sebagian", "location": "Sleman"}
    ]'::jsonb
),
-- 8. Valid Damage (Lampu LED)
(
    'SCE-8812341', 'ORD-QHM-008', 'SiCepat', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-15 10:00", "status": "Paket diserahkan ke kurir", "location": "Yogyakarta"},
        {"time": "2026-05-15 16:30", "status": "Diterima — box penyok basah terkena benturan cargo", "location": "Bantul"}
    ]'::jsonb
),
-- 9. Valid Damage (Water Heater)
(
    'JNE-9902341', 'ORD-QHM-009', 'JNE Trucking', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-18 08:30", "status": "Barang diserahkan ke cargo", "location": "Yogyakarta"},
        {"time": "2026-05-18 17:45", "status": "Terkirim — casing retak retak", "location": "Sleman"}
    ]'::jsonb
),
-- 10. Clean Delivery (Meja Makan - No Damage, Fraud Check!)
(
    'QHM-DEL-010331', 'ORD-QHM-010', 'Armada Qhomemart', 'delivered', 'intact', FALSE,
    '[
        {"time": "2026-05-16 09:00", "status": "Meja dimuat ke armada internal", "location": "Yogyakarta"},
        {"time": "2026-05-16 12:00", "status": "Tiba di lokasi penerima", "location": "Bantul"}
    ]'::jsonb
),
-- 11. Valid Damage (Kabel Roll)
(
    'QHM-DEL-011777', 'ORD-QHM-011', 'Armada Qhomemart', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-20 09:00", "status": "Barang diserahkan ke armada", "location": "Yogyakarta"},
        {"time": "2026-05-20 14:00", "status": "Terkirim — tergilas roda kendaraan di jalan", "location": "Sleman"}
    ]'::jsonb
),
-- 12. Valid Damage (Semen Tiga Roda)
(
    'QHM-DEL-012888', 'ORD-QHM-012', 'Dakota Cargo', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-19 10:00", "status": "Paket masuk drop point kargo", "location": "Yogyakarta"},
        {"time": "2026-05-19 16:30", "status": "Terkirim — kantong semen sobek parah terkena hujan", "location": "Yogyakarta"}
    ]'::jsonb
),
-- 13. Valid Damage (Bor Bosch)
(
    'QHM-DEL-013111', 'ORD-QHM-013', 'SiCepat', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-18 10:00", "status": "Paket masuk Hub", "location": "Yogyakarta"},
        {"time": "2026-05-18 15:45", "status": "Terkirim — box plastik retak parah", "location": "Sleman"}
    ]'::jsonb
),
-- 14. Valid Damage (Kipas Miyako)
(
    'QHM-DEL-014222', 'ORD-QHM-014', 'J&T Express', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-19 09:00", "status": "Kurir membawa paket", "location": "Yogyakarta"},
        {"time": "2026-05-19 14:00", "status": "Terkirim — leher kipas patah akibat guncangan", "location": "Yogyakarta"}
    ]'::jsonb
),
-- 15. Valid Damage (Cermin Dinding)
(
    'QHM-DEL-015333', 'ORD-QHM-015', 'GrabExpress', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-20 11:00", "status": "Driver pickup barang", "location": "Yogyakarta"},
        {"time": "2026-05-20 12:15", "status": "Tiba di tujuan — kaca cermin pecah 2 biji", "location": "Yogyakarta"}
    ]'::jsonb
),
-- 16. Valid Damage (Kitchen Sink Blanco)
(
    'QHM-DEL-016444', 'ORD-QHM-016', 'JNE Trucking', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-17 08:00", "status": "Diserahkan ke cargo", "location": "Yogyakarta"},
        {"time": "2026-05-18 16:30", "status": "Terkirim — stainless penyok pojok kiri", "location": "Sleman"}
    ]'::jsonb
),
-- 17. Valid Damage (Shower Set Toto)
(
    'QHM-DEL-017555', 'ORD-QHM-017', 'Armada Qhomemart', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-20 08:30", "status": "Loading ke truk armada", "location": "Yogyakarta"},
        {"time": "2026-05-20 11:45", "status": "Terkirim — hand shower retak bagian drat", "location": "Sleman"}
    ]'::jsonb
),
-- 18. Clean Delivery (Kuas Nippon - No Damage)
(
    'QHM-DEL-018666', 'ORD-QHM-018', 'GoSend', 'delivered', 'intact', FALSE,
    '[
        {"time": "2026-05-19 13:00", "status": "Tiba di lokasi penerima", "location": "Yogyakarta"}
    ]'::jsonb
),
-- 19. Valid Damage (Cat FTALIT)
(
    'QHM-DEL-019777', 'ORD-QHM-019', 'GrabExpress', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-18 10:00", "status": "Terkirim — kaleng bocor rembes", "location": "Bantul"}
    ]'::jsonb
),
-- 20. Valid Damage (Blender Philips)
(
    'QHM-DEL-020888', 'ORD-QHM-020', 'J&T Express', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-19 09:00", "status": "Diserahkan ke kurir", "location": "Yogyakarta"},
        {"time": "2026-05-19 15:30", "status": "Terkirim — gelas kaca blender pecah seribu", "location": "Bantul"}
    ]'::jsonb
),
-- 21. Clean Delivery (Obeng Set - No Damage)
(
    'QHM-DEL-021999', 'ORD-QHM-021', 'SiCepat', 'delivered', 'intact', FALSE,
    '[
        {"time": "2026-05-16 11:00", "status": "Terkirim", "location": "Ngaglik"}
    ]'::jsonb
),
-- 22. Clean Delivery (Stop Kontak Broco - No Damage)
(
    'QHM-DEL-022000', 'ORD-QHM-022', 'GoSend', 'delivered', 'intact', FALSE,
    '[
        {"time": "2026-05-20 14:00", "status": "Terkirim", "location": "Ngaglik"}
    ]'::jsonb
),
-- 23. Valid Damage (Wallpaper Dinding)
(
    'QHM-DEL-023111', 'ORD-QHM-023', 'J&T Express', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-18 09:00", "status": "Terkirim — roll wallpaper sobek tergores tajam", "location": "Sleman"}
    ]'::jsonb
),
-- 24. Valid Damage (Lemari Plastik)
(
    'QHM-DEL-024222', 'ORD-QHM-024', 'Armada Qhomemart', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-19 08:30", "status": "Dalam perjalanan", "location": "Yogyakarta"},
        {"time": "2026-05-19 12:00", "status": "Terkirim — panel pintu plastik retak 1 lembar", "location": "Sleman"}
    ]'::jsonb
),
-- 25. Clean Delivery (Jet Shower Toto - No Damage)
(
    'QHM-DEL-025333', 'ORD-QHM-025', 'GrabExpress', 'delivered', 'intact', FALSE,
    '[
        {"time": "2026-05-17 11:30", "status": "Terkirim", "location": "Sewon"}
    ]'::jsonb
),
-- 26. Valid Damage (Kompor Rinnai)
(
    'QHM-DEL-026444', 'ORD-QHM-026', 'Armada Qhomemart', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-20 09:00", "status": "Proses kirim", "location": "Yogyakarta"},
        {"time": "2026-05-20 11:15", "status": "Terkirim — kaca burner penyok & tungku goyang", "location": "Sewon"}
    ]'::jsonb
),
-- 27. Clean Delivery (Keramik Mulia - No Damage)
(
    'QHM-DEL-027555', 'ORD-QHM-027', 'Dakota Cargo', 'delivered', 'intact', FALSE,
    '[
        {"time": "2026-05-18 10:00", "status": "Terkirim", "location": "Sewon"}
    ]'::jsonb
),
-- 28. Valid Damage (Selang Air 15M)
(
    'QHM-DEL-028666', 'ORD-QHM-028', 'SiCepat', 'delivered_with_damage_report', 'intact', TRUE,
    '[
        {"time": "2026-05-17 10:00", "status": "Terkirim — selang tergores/bocor tertusuk paku cargo", "location": "Sewon"}
    ]'::jsonb
),
-- 29. Clean Delivery (Tang Tekiro - No Damage)
(
    'QHM-DEL-029777', 'ORD-QHM-029', 'GoSend', 'delivered', 'intact', FALSE,
    '[
        {"time": "2026-05-19 15:00", "status": "Terkirim", "location": "Sewon"}
    ]'::jsonb
),
-- 30. Clean Delivery (Saklar Panasonic - No Damage)
(
    'QHM-DEL-030888', 'ORD-QHM-030', 'GoSend', 'delivered', 'intact', FALSE,
    '[
        {"time": "2026-05-18 12:00", "status": "Terkirim", "location": "Terban"}
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
