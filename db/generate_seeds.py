# =============================================================================
# db/generate_seeds.py — Generates a massive 70-case sandbox dataset for Qhomemart
# =============================================================================
import os
import random

first_names = [
    "Budi", "Sari", "Agus", "Rina", "Dian", "Bambang", "Lina", "Hendra", "Dewi", "Andi",
    "Siti", "Joko", "Eka", "Fajar", "Gita", "Hadi", "Indah", "Kurniawan", "Lilis", "Mega",
    "Novianto", "Oki", "Putri", "Rian", "Siska", "Taufik", "Utami", "Vicky", "Wulan", "Yanto",
    "Zainal", "Ahmad", "Bayu", "Citra", "Dedi", "Erna", "Fitri", "Guntur", "Hany", "Iwan",
    "Julia", "Koko", "Lusi", "Maman", "Nina", "Oscar", "Prima", "Qori", "Rudi", "Santi",
    "Teguh", "Ujang", "Vina", "Wawan", "Yuni", "Zaki", "Adit", "Bella", "Candra", "Dina",
    "Edi", "Fani", "Gilang", "Hesti", "Indra", "Joni", "Kiki", "Lia", "Mita", "Novi", "Bagus"
]

last_names = [
    "Hartono", "Dewi", "Setiawan", "Wijaya", "Sasmita", "Triyono", "Marlina", "Pratama", "Aminah", "Susilo",
    "Rahmawati", "Nugroho", "Permata", "Syahputra", "Lestari", "Dwi", "Suryani", "Utami", "Eko", "Setiawan",
    "Handayani", "Hidayat", "Amelia", "Hidayat", "Ningsih", "Prasetyo", "Dari", "Saputra", "Wulandari", "Gunawan",
    "Siregar", "Lubis", "Tanjung", "Nasution", "Pane", "Batubara", "Harahap", "Pasaribu", "Pohan", "Pulungan"
]

addresses = [
    "Jl. Kaliurang Km 7, Sleman, Yogyakarta",
    "Jl. Gejayan No. 45, Yogyakarta",
    "Jl. Magelang Km 10, Sleman",
    "Jl. Monjali No. 12, Sleman, Yogyakarta",
    "Jl. Godean Km 4, Sleman, Yogyakarta",
    "Jl. Wates Km 2, Bantul, Yogyakarta",
    "Jl. Solo Km 12, Sleman, Yogyakarta",
    "Jl. Parangtritis Km 6, Bantul, Yogyakarta",
    "Jl. Ringroad Utara No. 12, Depok, Sleman",
    "Jl. Kusumanegara No. 88, Umbulharjo, Yogyakarta",
    "Jl. Affandi No. 10, Sleman, Yogyakarta",
    "Jl. Malioboro No. 25, Yogyakarta",
    "Jl. Gajah Mada No. 15, Danurejan, Yogyakarta",
    "Jl. Katamso No. 40, Mergangsan, Yogyakarta",
    "Jl. Kusumanegara No. 5, Yogyakarta",
    "Jl. Jenderal Sudirman No. 50, Yogyakarta",
    "Jl. Imogiri Timur Km 5, Bantul, Yogyakarta",
    "Jl. Wonosari Km 6, Banguntapan, Bantul",
    "Jl. Palagan No. 99, Ngaglik, Sleman",
    "Jl. Kaliurang Km 10, Ngaglik, Sleman",
    "Jl. Kabupaten No. 8, Sleman, Yogyakarta",
    "Jl. Magelang Km 6, Sleman, Yogyakarta",
    "Jl. Godean Km 7, Sleman, Yogyakarta",
    "Jl. Bantul Km 4, Dongkelan, Bantul",
    "Jl. Parangtritis Km 4, Sewon, Bantul",
    "Jl. Tamansiswa No. 120, Yogyakarta",
    "Jl. HOS Cokroaminoto No. 30, Yogyakarta",
    "Jl. Tajem Km 2, Maguwoharjo, Sleman",
    "Jl. Glagahsari No. 15, Umbulharjo, Yogyakarta",
    "Jl. C. Simanjuntak No. 10, Terban, Yogyakarta"
]

products_catalog = [
    # Category, Name, Price, Location, Warehouse Condition
    ("Bahan Bangunan", "Granit Lantai Niro Granite 60x60 (Dus)", 250000.00, "Gudang Utama A1", "good"),
    ("Bahan Bangunan", "Semen Instan Mortar Utama (MU-380) 40kg", 85000.00, "Gudang Material B2", "depleted"),
    ("Furnitur", "Rak Dinding Minimalis Kayu", 150000.00, "Gudang Furnitur F1", "good"),
    ("Sanitary", "Kloset Duduk Toto Eco Washer Tipe CW421J", 2400000.00, "Gudang Sanitary D3", "damaged_in_warehouse"),
    ("Furnitur", "Sofa Minimalis L-Shape Fabric (Abu-abu)", 5500000.00, "Gudang Furnitur F1", "damaged_in_warehouse"),
    ("Cat & Perlengkapan", "Cat Tembok Dulux Catylac Putih 5kg", 160000.00, "Gudang Cat C1", "good"),
    ("Sanitary", "Keran Air Cabang Stainless", 95000.00, "Gudang Sanitary D3", "good"),
    ("Kelistrikan", "Lampu LED Philips 12W (Pack isi 4)", 120000.00, "Gudang Listrik E2", "good"),
    ("Sanitary", "Water Heater Ariston 15L Tipe Andris2 R", 2250000.00, "Gudang Sanitary D3", "good"),
    ("Furnitur", "Meja Makan Kayu Jati Minimalis", 3500000.00, "Gudang Furnitur F1", "good"),
    ("Kelistrikan", "Kabel Roll Panasonic 10 Meter", 180000.00, "Gudang Listrik E2", "good"),
    ("Bahan Bangunan", "Semen Tiga Roda 40kg", 65000.00, "Gudang Material B2", "good"),
    ("Tools", "Bor Listrik Bosch GSB 550", 680000.00, "Gudang Perkakas G1", "good"),
    ("Peralatan Rumah Tangga", "Kipas Angin Stand Miyako", 250000.00, "Gudang Elektronik H2", "good"),
    ("Dekorasi", "Cermin Dinding Hexagonal (Set isi 6)", 120000.00, "Gudang Dekorasi J3", "good"),
    ("Dapur", "Kitchen Sink Blanco Stainless", 1850000.00, "Gudang Sanitary D3", "good"),
    ("Sanitary", "Shower Column Set Toto", 3200000.00, "Gudang Sanitary D3", "good"),
    ("Cat & Perlengkapan", "Kuas Cat Nippon Paint 3 Inch", 15000.00, "Gudang Cat C1", "good"),
    ("Cat & Perlengkapan", "Cat Kayu & Besi FTALIT 1kg", 75000.00, "Gudang Cat C1", "good"),
    ("Peralatan Rumah Tangga", "Blender Philips HR2115", 650000.00, "Gudang Elektronik H2", "good"),
    ("Tools", "Obeng Set Kenmaster 31 in 1", 45000.00, "Gudang Perkakas G1", "good"),
    ("Kelistrikan", "Stop Kontak Broco 4 Lubang", 85000.00, "Gudang Listrik E2", "good"),
    ("Dekorasi", "Wallpaper Dinding 3D Foam (Roll)", 35000.00, "Gudang Dekorasi J3", "good"),
    ("Furnitur", "Lemari Pakaian Plastik Club 4 Susun", 280000.00, "Gudang Furnitur F1", "good"),
    ("Sanitary", "Jet Shower Closet Toto", 195000.00, "Gudang Sanitary D3", "good"),
    ("Dapur", "Kompor Gas Rinnai 2 Tungku", 420000.00, "Gudang Dapur K1", "good"),
    ("Lantai", "Keramik Lantai Mulia 40x40 (Dus)", 60000.00, "Gudang Utama A1", "good"),
    ("Taman", "Selang Air Anti Tekuk 15 Meter", 110000.00, "Gudang Taman L2", "good"),
    ("Tools", "Tang Kombinasi Tekiro 7 Inch", 55000.00, "Gudang Perkakas G1", "good"),
    ("Kelistrikan", "Saklar Lampu Panasonic Single", 18000.00, "Gudang Listrik E2", "good"),
    ("Tools", "Palu Kambing Tekiro 16 oz", 75000.00, "Gudang Perkakas G1", "good"),
    ("Sanitary", "Wastafel Gantung Toto", 450000.00, "Gudang Sanitary D3", "good"),
    ("Bahan Bangunan", "Dempul Kayu Isamu 1kg", 45000.00, "Gudang Cat C1", "good"),
    ("Dapur", "Rice Cooker Miyako 1.8L", 280000.00, "Gudang Elektronik H2", "good"),
    ("Dekorasi", "Pot Bunga Keramik Putih", 65000.00, "Gudang Taman L2", "good"),
    ("Tools", "Kunci Inggris Tekiro 10 Inch", 115000.00, "Gudang Perkakas G1", "good"),
    ("Dapur", "Mixer Cosmos Stand", 350000.00, "Gudang Elektronik H2", "good"),
    ("Rumah Tangga", "Setrika Listrik Philips Tipe HD1173", 295000.00, "Gudang Elektronik H2", "good"),
    ("Taman", "Gunting Dahan Tekiro", 85000.00, "Gudang Taman L2", "good"),
    ("Bahan Bangunan", "Thinner Impala 1 Liter", 35000.00, "Gudang Cat C1", "good"),
    ("Kelistrikan", "Kabel Antena TV coaxial 15M", 55000.00, "Gudang Listrik E2", "good"),
    ("Furnitur", "Kursi Kantor Ergonomis", 850000.00, "Gudang Furnitur F1", "good"),
    ("Dapur", "Teflon Maxim 24cm", 125000.00, "Gudang Dapur K1", "good"),
    ("Dekorasi", "Gantungan Baju Kayu (Set isi 10)", 48000.00, "Gudang Dekorasi J3", "good"),
    ("Taman", "Sekop Mini Taman Stainless", 35000.00, "Gudang Taman L2", "good"),
    ("Rumah Tangga", "Sapu Lantai nilon Kurma", 28000.00, "Gudang Utama A1", "good"),
    ("Sanitary", "Selang Shower Toto 1.5 Meter", 85000.00, "Gudang Sanitary D3", "good"),
    ("Kelistrikan", "Bohlam LED Philips 19W", 95000.00, "Gudang Listrik E2", "good"),
    ("Bahan Bangunan", "Gergaji Kayu Tekiro 18 Inch", 68000.00, "Gudang Perkakas G1", "good"),
    ("Dapur", "Rak Piring Aluminium 3 Susun", 380000.00, "Gudang Furnitur F1", "good"),
    ("Rumah Tangga", "Pel Set Alat Pel Spin Mop", 195000.00, "Gudang Utama A1", "good"),
    ("Furnitur", "Meja Kerja Minimalis", 950000.00, "Gudang Furnitur F1", "good"),
    ("Tools", "Meteran Tekiro 5 Meter", 40000.00, "Gudang Perkakas G1", "good"),
    ("Kelistrikan", "Fitting Lampu Panasonic Gantung", 12000.00, "Gudang Listrik E2", "good"),
    ("Sanitary", "Bak Cuci Piring Stainless Royal", 450000.00, "Gudang Sanitary D3", "good"),
    ("Dekorasi", "Lukisan Dinding Canvas Modern", 180000.00, "Gudang Dekorasi J3", "good"),
    ("Rumah Tangga", "Tempat Sampah Injak 10L Plastik", 45000.00, "Gudang Utama A1", "good"),
    ("Bahan Bangunan", "Paku Kayu 3 Inch (1kg)", 25000.00, "Gudang Material B2", "good"),
    ("Taman", "Pupuk Organik Cair 1 Liter", 35000.00, "Gudang Taman L2", "good"),
    ("Dapur", "Dispenser Miyako Hot & Normal", 185000.00, "Gudang Elektronik H2", "good")
]

couriers = ["Armada Qhomemart", "Dakota Cargo", "J&T Express", "SiCepat", "JNE Trucking", "GoSend", "GrabExpress", "Indah Logistik"]

sql_content = """-- =============================================================================
-- db/seed.sql — Expanded Qhomemart Dummy Data (70 Fully Mapped Sandbox Cases)
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
"""

# Generate 70 Customers (CUST-001 s/d CUST-070) plus CUST-999
customer_rows = []
for i in range(1, 71):
    c_id = f"CUST-{i:03d}"
    first = first_names[(i - 1) % len(first_names)]
    last = last_names[(i - 1) % len(last_names)]
    name = f"{first} {last}"
    email = f"{first.lower()}.{last.lower()}{i}@email.com"
    phone = f"0812{random.randint(10000000, 99999999)}"
    addr = addresses[(i - 1) % len(addresses)]
    is_loyal = "TRUE" if i % 3 == 0 else "FALSE"
    clv = round(random.uniform(50000, 150000000), 2)
    tot_orders = random.randint(1, 50)
    prev_comp = random.randint(0, 3)
    customer_rows.append(f"('{c_id}', '{name}', '{email}', '{phone}', '{addr}', {is_loyal}, {clv:.2f}, {tot_orders}, {prev_comp})")

customer_rows.append("('CUST-999', 'Pelanggan Baru', 'newbie@email.com', '081199998888', 'Bantul, Yogyakarta', FALSE, 0.00, 1, 0)")
sql_content += ",\n".join(customer_rows) + ";\n\n"

sql_content += """-- -----------------------------------------------------------------------------
-- 2. PRODUCTS
-- -----------------------------------------------------------------------------
INSERT INTO products (product_id, category, product_name, price_idr, stock_available, warehouse_location, warehouse_condition) VALUES
"""

# Generate Products (PRD-001 s/d PRD-070)
product_rows = []
for i in range(1, 71):
    p_id = f"PRD-{i:03d}"
    p_info = products_catalog[(i - 1) % len(products_catalog)]
    cat, name, price, loc, cond = p_info
    stock = 0 if i == 2 else random.randint(3, 150)
    
    # Keep predefined conditions for special ones
    if i == 4 or i == 5:
        cond = "damaged_in_warehouse"
    elif i == 2:
        cond = "depleted"
        
    product_rows.append(f"('{p_id}', '{cat}', '{name}', {price:.2f}, {stock}, '{loc}', '{cond}')")

sql_content += ",\n".join(product_rows) + ";\n\n"

sql_content += """-- -----------------------------------------------------------------------------
-- 3. ORDERS
-- -----------------------------------------------------------------------------
INSERT INTO orders (order_id, customer_id, order_date, total_amount_idr, status) VALUES
"""

# Generate 70 Orders (ORD-QHM-001 s/d ORD-QHM-070)
order_rows = []
for i in range(1, 71):
    o_id = f"ORD-QHM-{i:03d}"
    c_id = "CUST-999" if i == 2 else f"CUST-{i:03d}"
    days_ago = random.randint(1, 10)
    
    # Calculate price based on product
    p_info = products_catalog[(i - 1) % len(products_catalog)]
    price = p_info[2]
    qty = 2 if i == 6 or i == 8 else (3 if i == 12 else 1)
    subtotal = price * qty
    
    status = "pending" if i == 2 else "delivered"
    order_rows.append(f"('{o_id}', '{c_id}', NOW() - INTERVAL '{days_ago} days', {subtotal:.2f}, '{status}')")

sql_content += ",\n".join(order_rows) + ";\n\n"

sql_content += """-- -----------------------------------------------------------------------------
-- 4. ORDER ITEMS
-- -----------------------------------------------------------------------------
INSERT INTO order_items (order_id, product_id, quantity, subtotal_idr) VALUES
"""

# Generate 70 Order Items
item_rows = []
for i in range(1, 71):
    o_id = f"ORD-QHM-{i:03d}"
    p_id = f"PRD-{i:03d}"
    qty = 2 if i == 6 or i == 8 else (3 if i == 12 else 1)
    p_info = products_catalog[(i - 1) % len(products_catalog)]
    price = p_info[2]
    subtotal = price * qty
    item_rows.append(f"('{o_id}', '{p_id}', {qty}, {subtotal:.2f})")

sql_content += ",\n".join(item_rows) + ";\n\n"

sql_content += """-- -----------------------------------------------------------------------------
-- 5. DELIVERIES (Logistik Kurir / 70 Mapped Sandboxes)
-- -----------------------------------------------------------------------------
INSERT INTO deliveries (tracking_id, order_id, courier_name, status, condition_on_pickup, damage_reported_by_courier, delivery_logs) VALUES
"""

# Generate 70 Deliveries
delivery_rows = []
for i in range(1, 71):
    o_id = f"ORD-QHM-{i:03d}"
    tracking_id = f"QHM-DEL-{i:03d}{random.randint(1000, 9999)}"
    
    courier = couriers[(i - 1) % len(couriers)]
    
    # Specific statuses for rich sandbox scenarios:
    # We will make 70% of deliveries have valid damage reports, and 30% clean for fraud checks.
    is_damaged = True
    if i % 3 == 0 or i % 7 == 0:
        is_damaged = False
        
    # Standard overrides for previous sandbox test consistency
    if i == 2: # Pending stock out
        status = "pending"
        pickup_cond = "intact"
        reported_damage = "FALSE"
        logs = '[{"time": "2026-05-20 08:00", "status": "Ditunda — menunggu restock pabrik", "location": "Gudang B2"}]'
    elif i == 10 or i == 18 or i == 21 or i == 22 or i == 25 or i == 27 or i == 29 or i == 30:
        is_damaged = False
        status = "delivered"
        pickup_cond = "intact"
        reported_damage = "FALSE"
        logs = '[{"time": "2026-05-19 13:00", "status": "Terkirim bersih, packing mulus", "location": "Yogyakarta"}]'
    elif is_damaged:
        status = "delivered_with_damage_report"
        pickup_cond = "intact"
        reported_damage = "TRUE"
        logs = '[{"time": "2026-05-19 09:00", "status": "Barang diserahkan ke kurir", "location": "Yogyakarta"}, {"time": "2026-05-19 14:30", "status": "Terkirim — terdeteksi benturan parah/kerusakan fisik oleh kurir", "location": "Yogyakarta"}]'
    else:
        status = "delivered"
        pickup_cond = "intact"
        reported_damage = "FALSE"
        logs = '[{"time": "2026-05-19 10:00", "status": "Tiba di lokasi tujuan, diterima penerima", "location": "Yogyakarta"}]'
        
    delivery_rows.append(f"('{tracking_id}', '{o_id}', '{courier}', '{status}', '{pickup_cond}', {reported_damage}, '{logs}'::jsonb)")

sql_content += ",\n".join(delivery_rows) + ";\n\n"

sql_content += """-- -----------------------------------------------------------------------------
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
"""

# Write to seed.sql
with open(os.path.join(os.path.dirname(__file__), "seed.sql"), "w") as f:
    f.write(sql_content)

print("SUCCESSFULLY GENERATED 70 SANDBOX SKENARIOS!")
