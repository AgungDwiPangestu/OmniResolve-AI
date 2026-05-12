-- =============================================================================
-- db/seed.sql — Sample Data untuk Demo & Testing
-- =============================================================================

-- Seed beberapa sesi contoh untuk demo kepada juri
INSERT INTO complaint_sessions (
    session_id, raw_input, customer_id, order_id, complaint_type,
    sentiment_score, claim_valid, stock_status, decision_type,
    compensation_value_idr, requires_human_approval, chain_of_thought,
    final_response, status
) VALUES
(
    'demo-session-001',
    'Barang saya datang dalam kondisi rusak parah. Lemari yang saya pesan pecah di bagian pintu. Tolong diproses segera! Order saya ORD-004.',
    'CUST-001',
    'ORD-004',
    'damaged_item',
    -0.85,
    TRUE,
    'damaged_in_warehouse',
    'replacement',
    0,
    FALSE,
    'Reasoning: Pelanggan setia (CLV Rp 15jt, 23 pesanan). Audit mengonfirmasi kerusakan terjadi saat transit (laporan kurir JNT-5590234). Kompensasi: kirim pengganti + pickup barang rusak.',
    'Yth. Bapak/Ibu Budi Hartono, kami sangat menyesal atas ketidaknyamanan ini. Kami telah menjadwalkan pengiriman lemari pengganti dan pickup barang rusak untuk besok pukul 09:00-12:00. Tidak ada biaya tambahan untuk Anda.',
    'completed'
),
(
    'demo-session-002',
    'Beli rak dinding ORD-003, barang gak sesuai foto. Warnanya beda.',
    'CUST-002',
    'ORD-003',
    'wrong_item',
    -0.45,
    TRUE,
    'available',
    'voucher',
    75000,
    FALSE,
    'Reasoning: Pelanggan baru (2 pesanan, CLV Rp 250rb). Harga barang Rp 350rb. Opsi konservatif: voucher diskon 20% untuk pembelian berikutnya.',
    'Halo, mohon maaf atas ketidaksesuaian produk yang Anda terima. Kami telah menerbitkan voucher diskon Rp 75.000 yang berlaku untuk pembelian berikutnya. Voucher akan dikirim ke email Anda dalam 1 jam.',
    'completed'
)
ON CONFLICT (session_id) DO NOTHING;
