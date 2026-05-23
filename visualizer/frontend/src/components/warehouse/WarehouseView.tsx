"use client";

import { useState, useEffect, useCallback } from "react";
import { useNavigationStore } from "@/stores/navigationStore";

function getApiUrl(): string {
  return (process.env.NEXT_PUBLIC_OMNI_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
}

interface ProductStock {
  product_id: string;
  category: string | null;
  product_name: string;
  price_idr: number;
  stock_available: number;
  warehouse_location: string | null;
  warehouse_condition: string;
}

interface StockMovement {
  id: number;
  product_id: string;
  product_name: string;
  movement_type: string;
  quantity: number;
  reason: string | null;
  order_id: string | null;
  created_at: string;
}

function stockBadge(stock: number, condition: string) {
  if (condition === "depleted" || stock === 0)
    return <span className="px-2 py-0.5 rounded text-xs font-bold bg-red-900/60 text-red-300 border border-red-700">HABIS</span>;
  if (condition === "damaged_in_warehouse")
    return <span className="px-2 py-0.5 rounded text-xs font-bold bg-orange-900/60 text-orange-300 border border-orange-700">RUSAK</span>;
  if (stock <= 10)
    return <span className="px-2 py-0.5 rounded text-xs font-bold bg-yellow-900/60 text-yellow-300 border border-yellow-700">RENDAH</span>;
  return <span className="px-2 py-0.5 rounded text-xs font-bold bg-green-900/60 text-green-300 border border-green-700">OK</span>;
}

function movementBadge(type: string) {
  if (type === "in" || type === "po_received")
    return <span className="px-2 py-0.5 rounded text-xs font-bold bg-green-900/50 text-green-300 border border-green-800">IN ↑</span>;
  if (type === "write_off")
    return <span className="px-2 py-0.5 rounded text-xs font-bold bg-slate-700 text-slate-400 border border-slate-600">WRITE-OFF</span>;
  return <span className="px-2 py-0.5 rounded text-xs font-bold bg-red-900/50 text-red-300 border border-red-800">OUT ↓</span>;
}

function formatRp(v: number) {
  return "Rp " + v.toLocaleString("id-ID");
}

export function WarehouseView(): React.ReactNode {
  const goToBuilding = useNavigationStore((s) => s.goToBuilding);

  const [products, setProducts] = useState<ProductStock[]>([]);
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "ok" | "low" | "depleted" | "damaged">("all");
  const [search, setSearch] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [pRes, mRes] = await Promise.all([
        fetch(`${getApiUrl()}/api/v1/admin/inventory/products`),
        fetch(`${getApiUrl()}/api/v1/admin/inventory/movements?limit=50`),
      ]);
      if (pRes.ok) setProducts(await pRes.json() as ProductStock[]);
      if (mRes.ok) setMovements(await mRes.json() as StockMovement[]);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void fetchData(); }, [fetchData]);

  const filtered = products.filter((p) => {
    const matchSearch = search === "" || p.product_name.toLowerCase().includes(search.toLowerCase()) || (p.category ?? "").toLowerCase().includes(search.toLowerCase());
    if (!matchSearch) return false;
    if (filter === "ok") return p.stock_available > 10 && p.warehouse_condition === "good";
    if (filter === "low") return p.stock_available > 0 && p.stock_available <= 10;
    if (filter === "depleted") return p.stock_available === 0 || p.warehouse_condition === "depleted";
    if (filter === "damaged") return p.warehouse_condition === "damaged_in_warehouse";
    return true;
  });

  const total = products.length;
  const okCount = products.filter((p) => p.stock_available > 10 && p.warehouse_condition === "good").length;
  const lowCount = products.filter((p) => p.stock_available > 0 && p.stock_available <= 10).length;
  const depletedCount = products.filter((p) => p.stock_available === 0 || p.warehouse_condition === "depleted").length;
  const damagedCount = products.filter((p) => p.warehouse_condition === "damaged_in_warehouse").length;

  return (
    <div className="flex flex-col h-full bg-slate-950 text-white overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 flex-shrink-0">
        <button onClick={goToBuilding} className="flex items-center gap-2 text-slate-400 hover:text-white text-sm font-mono transition-colors group">
          <span className="group-hover:-translate-x-0.5 transition-transform">←</span>
          <span>Pilih Lantai</span>
        </button>
        <div className="flex items-center gap-2">
          <span className="text-lg">📦</span>
          <span className="text-white font-bold">Warehouse</span>
          <span className="text-slate-600 font-mono text-xs hidden sm:block">— Inventory Control</span>
        </div>
        <button onClick={() => void fetchData()} className="text-xs text-slate-500 hover:text-green-400 font-mono transition-colors">
          ↻ Refresh
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">

        {/* Summary cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Total SKU", value: total, color: "text-white", bg: "bg-slate-800 border-slate-700" },
            { label: "Stok OK", value: okCount, color: "text-green-400", bg: "bg-green-900/20 border-green-800" },
            { label: "Stok Rendah", value: lowCount, color: "text-yellow-400", bg: "bg-yellow-900/20 border-yellow-800" },
            { label: "Habis/Rusak", value: depletedCount + damagedCount, color: "text-red-400", bg: "bg-red-900/20 border-red-800" },
          ].map((c) => (
            <div key={c.label} className={`rounded-xl border p-4 ${c.bg}`}>
              <p className="text-xs text-slate-500 font-mono uppercase tracking-widest">{c.label}</p>
              <p className={`text-3xl font-bold mt-1 ${c.color}`}>{loading ? "—" : c.value}</p>
            </div>
          ))}
        </div>

        {/* Filter + Search */}
        <div className="flex flex-wrap gap-2 items-center">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Cari produk atau kategori..."
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white font-mono outline-none focus:border-green-500 transition-colors placeholder:text-slate-600 w-56"
          />
          {(["all", "ok", "low", "depleted", "damaged"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-xs font-mono px-3 py-1.5 rounded-lg border transition-colors ${
                filter === f
                  ? "bg-green-500 text-slate-900 border-green-500 font-bold"
                  : "border-slate-700 text-slate-500 hover:text-slate-300 hover:border-slate-500"
              }`}
            >
              {f === "all" ? "Semua" : f === "ok" ? "OK" : f === "low" ? "Rendah" : f === "depleted" ? "Habis" : "Rusak"}
            </button>
          ))}
        </div>

        {/* Products table */}
        <section>
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest font-mono mb-3">
            Daftar Produk ({filtered.length})
          </h2>
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm font-mono">
                <thead>
                  <tr className="border-b border-slate-800 text-xs text-slate-500 uppercase tracking-widest">
                    <th className="text-left px-4 py-3">Produk</th>
                    <th className="text-left px-4 py-3">Kategori</th>
                    <th className="text-right px-4 py-3">Harga</th>
                    <th className="text-right px-4 py-3">Stok</th>
                    <th className="text-center px-4 py-3">Status</th>
                    <th className="text-left px-4 py-3 hidden md:table-cell">Gudang</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr><td colSpan={6} className="text-center py-8 text-slate-600 italic">Loading...</td></tr>
                  ) : filtered.length === 0 ? (
                    <tr><td colSpan={6} className="text-center py-8 text-slate-600 italic">Tidak ada produk</td></tr>
                  ) : filtered.map((p) => (
                    <tr key={p.product_id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-3 text-white">{p.product_name}</td>
                      <td className="px-4 py-3 text-slate-400">{p.category ?? "—"}</td>
                      <td className="px-4 py-3 text-right text-slate-300">{formatRp(p.price_idr)}</td>
                      <td className={`px-4 py-3 text-right font-bold ${p.stock_available === 0 ? "text-red-400" : p.stock_available <= 10 ? "text-yellow-400" : "text-green-400"}`}>
                        {p.stock_available}
                      </td>
                      <td className="px-4 py-3 text-center">{stockBadge(p.stock_available, p.warehouse_condition)}</td>
                      <td className="px-4 py-3 text-slate-500 text-xs hidden md:table-cell">{p.warehouse_location ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Recent movements */}
        <section>
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest font-mono mb-3">
            Histori Pergerakan Stok (50 Terakhir)
          </h2>
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm font-mono">
                <thead>
                  <tr className="border-b border-slate-800 text-xs text-slate-500 uppercase tracking-widest">
                    <th className="text-left px-4 py-3">Waktu</th>
                    <th className="text-left px-4 py-3">Produk</th>
                    <th className="text-center px-4 py-3">Tipe</th>
                    <th className="text-right px-4 py-3">Qty</th>
                    <th className="text-left px-4 py-3">Alasan</th>
                    <th className="text-left px-4 py-3 hidden md:table-cell">Order</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr><td colSpan={6} className="text-center py-8 text-slate-600 italic">Loading...</td></tr>
                  ) : movements.length === 0 ? (
                    <tr><td colSpan={6} className="text-center py-8 text-slate-600 italic">Belum ada pergerakan stok</td></tr>
                  ) : movements.map((m) => (
                    <tr key={m.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-2.5 text-slate-500 text-xs">{m.created_at.slice(0, 16).replace("T", " ")}</td>
                      <td className="px-4 py-2.5 text-white text-xs">{m.product_name}</td>
                      <td className="px-4 py-2.5 text-center">{movementBadge(m.movement_type)}</td>
                      <td className="px-4 py-2.5 text-right font-bold text-slate-200">{m.quantity}</td>
                      <td className="px-4 py-2.5 text-slate-400 text-xs">{m.reason ?? "—"}</td>
                      <td className="px-4 py-2.5 text-slate-600 text-xs hidden md:table-cell">{m.order_id ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
