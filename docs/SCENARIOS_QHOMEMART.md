# Skenario Resolusi Konflik (SOP Qhomemart)
Dokumen ini berisi panduan resmi dan skenario bisnis yang digunakan oleh **OmniResolve-AI** untuk menangani keluhan pelanggan secara otomatis. AI (Strategic Negotiator) telah dikonfigurasi untuk mematuhi aturan ini secara ketat.

## 1. Barang Rusak Saat Pengiriman (Fisik)
**Konteks**: Barang rentan pecah belah (keramik, kloset, cermin) atau barang furnitur rusak akibat cuaca/handling kurir (contoh: Sofa basah karena terpal bocor).
- **Validasi Klaim**: Auditor akan mengecek log kurir (misal: "Catatan: basah/kotor", "packing kayu rusak").
- **Tindakan AI**: 
  - `Decision`: **Replacement** (Ganti Baru).
  - Agen Orchestrator akan memesan armada kurir (biasanya Armada Internal Qhomemart) untuk menarik barang lama dan mengirimkan barang baru.
  - **Dilarang**: AI tidak boleh hanya menawarkan voucher untuk kerusakan fisik. Jika pelanggan memaksa, AI akan tetap mengutamakan *replacement*.

## 2. Salah Kirim / Barang Tidak Sesuai (Kesalahan Gudang)
**Konteks**: Pelanggan memesan Cat Nippon Paint Putih, namun yang dikirim Cat Jotun Abu-abu, atau Granit ukuran 60x60 tapi yang dikirim 80x80.
- **Validasi Klaim**: Auditor mengecek ketidakcocokan antara Order ID dan foto/deskripsi keluhan.
- **Tindakan AI**:
  - `Decision`: **Replacement** (Tarik barang salah, kirim barang benar).
  - `Kompensasi Tambahan`: AI akan memberikan **Voucher Ekstra** (sekitar Rp 50.000 - Rp 100.000) sebagai bentuk permintaan maaf atas kesalahan internal perusahaan (Human Error).

## 3. Barang Kurang (Partial Delivery)
**Konteks**: Pelanggan membeli 10 dus keramik lantai, namun kurir hanya mengantarkan 9 dus.
- **Validasi Klaim**: Pengecekan manifest pengiriman dan catatan penerimaan.
- **Tindakan AI**:
  - `Decision`: **Replacement** (Faktanya: Pengiriman Susulan / melengkapi kekurangan).
  - ERP akan mengurangi stok sebanyak 1 buah, dan kurir dijadwalkan untuk mengirim sisa barang.

## 4. Keterlambatan Pengiriman (Late Delivery)
**Konteks**: Janji kirim tanggal 12, tapi sampai tanggal 15 barang belum tiba.
- **Validasi Klaim**: Auditor mengecek status "on_process" atau "on_delivery" yang sudah melewati SLA.
- **Tindakan AI**:
  - `Decision`: **Voucher** (Diskon atau Gratis Ongkir).
  - Nilai voucher bergantung pada harga barang dan Customer Lifetime Value (CLV). Semakin tinggi CLV, nilai voucher keterlambatan bisa lebih besar.

## 5. Stok Habis (Out of Stock / Ghost Inventory)
**Konteks**: Pelanggan sudah membayar lunas, tapi saat barang mau dikirim, stok di toko/gudang ternyata habis atau cacat (tidak layak jual).
- **Validasi Klaim**: Auditor mengecek `stock_available = 0` dari database PostgreSQL.
- **Tindakan AI**:
  - `Decision`: **Refund** (Pengembalian Dana Penuh).
  - ERP tool akan memicu `process_refund` yang mengubah status pesanan pelanggan menjadi "refunded".

## 6. Klaim Palsu / Tidak Valid (Fraud/User Error)
**Konteks**: Pelanggan mengklaim cermin pecah saat pengiriman, padahal log kurir mencatat barang utuh saat diserahterimakan, atau kerusakan jelas akibat kesalahan perakitan pelanggan (User Error).
- **Validasi Klaim**: Log kurir tidak mendukung klaim, atau tidak ada bukti.
- **Tindakan AI**:
  - `Decision`: **Reject** (Tolak klaim).
  - Pesan balasan AI: Akan disusun dengan bahasa yang sangat sopan, menjelaskan bukti bahwa barang utuh saat serah terima, serta menawarkan solusi alternatif (seperti panduan servis garansi pabrik atau perbaikan berbayar).

---

## Aturan Tambahan (Customer Lifetime Value - CLV & HITL)
* **Pelanggan Setia (VIP)**: Jika pelanggan memiliki histori belanja > 5 Juta atau flag `is_loyal = TRUE`, AI akan memberikan layanan prioritas (nilai voucher lebih besar, atau toleransi klaim lebih longgar).
* **Human-in-the-Loop (HITL)**: Jika nilai barang yang diganti atau voucher kompensasi bernilai di atas Rp 1.000.000, AI wajib mengatur `requires_human_approval = True`. Sistem akan mem-pause aksi (pending_hitl) dan mengirim notifikasi ke Supervisor.
