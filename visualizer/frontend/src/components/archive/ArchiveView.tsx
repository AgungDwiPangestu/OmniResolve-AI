"use client";

import { useState, useEffect, useCallback } from "react";
import { useNavigationStore } from "@/stores/navigationStore";

// ============================================================================
// TYPES
// ============================================================================

const COLLECTIONS = [
  { id: "sop_policies", label: "SOP & Kebijakan", description: "Aturan bisnis dan SOP Qhomemart" },
  { id: "faq_patterns", label: "Pola FAQ", description: "Pola keluhan umum dan respons ideal" },
  { id: "product_catalog", label: "Katalog Produk", description: "Info produk, kategori, garansi" },
  { id: "resolved_cases", label: "Kasus Selesai", description: "Diisi otomatis oleh feedback loop" },
] as const;

type CollectionId = (typeof COLLECTIONS)[number]["id"];

interface CollectionStats {
  description: string;
  document_count: number;
}

// ============================================================================
// HELPERS
// ============================================================================

function getApiUrl(): string {
  return (process.env.NEXT_PUBLIC_OMNI_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
}

// ============================================================================
// STATS CARD
// ============================================================================

function StatsCard({
  collectionId,
  stats,
}: {
  collectionId: string;
  stats: CollectionStats | null;
}): React.ReactNode {
  const col = COLLECTIONS.find((c) => c.id === collectionId);
  const isAuto = collectionId === "resolved_cases";
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs text-slate-500 font-mono uppercase tracking-wide">
            {col?.label ?? collectionId}
          </p>
          <p className="text-2xl font-bold text-white mt-1">
            {stats === null ? "—" : stats.document_count < 0 ? "0" : stats.document_count}
          </p>
        </div>
        {isAuto && (
          <span className="text-xs bg-emerald-900/50 text-emerald-400 border border-emerald-700 rounded px-2 py-0.5 font-mono">
            AUTO
          </span>
        )}
      </div>
      <p className="text-xs text-slate-600 mt-2">{col?.description}</p>
    </div>
  );
}

// ============================================================================
// MAIN ARCHIVE VIEW
// ============================================================================

export function ArchiveView(): React.ReactNode {
  const goToBuilding = useNavigationStore((s) => s.goToBuilding);
  const lockArchive = useNavigationStore((s) => s.lockArchive);

  // Stats
  const [stats, setStats] = useState<Record<string, CollectionStats> | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);

  // Form state
  const [selectedCollection, setSelectedCollection] = useState<CollectionId>("sop_policies");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("");
  const [source, setSource] = useState("");
  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitResult, setSubmitResult] = useState<{ ok: boolean; message: string } | null>(null);

  // Seed
  const [seedLoading, setSeedLoading] = useState(false);
  const [seedResult, setSeedResult] = useState<string | null>(null);

  // Clear collection
  const [clearTarget, setClearTarget] = useState<string | null>(null);
  const [clearLoading, setClearLoading] = useState(false);

  // -------------------------------------------------------------------------
  // Fetch stats
  // -------------------------------------------------------------------------

  const fetchStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/admin/knowledge/stats`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as { collections: Record<string, CollectionStats> };
      setStats(data.collections);
    } catch (e) {
      console.error("stats fetch error", e);
      setStats(null);
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchStats();
  }, [fetchStats]);

  // -------------------------------------------------------------------------
  // Seed
  // -------------------------------------------------------------------------

  const handleSeed = async () => {
    setSeedLoading(true);
    setSeedResult(null);
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/admin/knowledge/seed`, { method: "POST" });
      const data = (await res.json()) as { message: string; total_ingested: number };
      setSeedResult(`✓ ${data.message} (${data.total_ingested} dokumen)`);
      void fetchStats();
    } catch (e) {
      setSeedResult(`✗ Seed gagal: ${String(e)}`);
    } finally {
      setSeedLoading(false);
    }
  };

  // -------------------------------------------------------------------------
  // Ingest document
  // -------------------------------------------------------------------------

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    setSubmitLoading(true);
    setSubmitResult(null);

    const metadata: Record<string, string> = {};
    if (category.trim()) metadata.category = category.trim();
    if (source.trim()) metadata.source = source.trim();

    try {
      const res = await fetch(`${getApiUrl()}/api/v1/admin/knowledge/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          collection: selectedCollection,
          documents: [{ content: content.trim(), metadata }],
        }),
      });
      if (!res.ok) {
        const err = (await res.json()) as { detail: string };
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }
      const data = (await res.json()) as { ingested_count: number; collection: string };
      setSubmitResult({ ok: true, message: `${data.ingested_count} dokumen berhasil ditambahkan ke '${data.collection}'.` });
      setContent("");
      setCategory("");
      setSource("");
      void fetchStats();
    } catch (e) {
      setSubmitResult({ ok: false, message: `Gagal: ${String(e)}` });
    } finally {
      setSubmitLoading(false);
    }
  };

  // -------------------------------------------------------------------------
  // Clear collection
  // -------------------------------------------------------------------------

  const handleClear = async (collectionId: string) => {
    setClearLoading(true);
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/admin/knowledge/${collectionId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setClearTarget(null);
      void fetchStats();
    } catch (e) {
      alert(`Gagal menghapus: ${String(e)}`);
    } finally {
      setClearLoading(false);
    }
  };

  // -------------------------------------------------------------------------
  // RENDER
  // -------------------------------------------------------------------------

  return (
    <div className="flex flex-col h-full bg-slate-950 text-white overflow-y-auto">
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 flex-shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={goToBuilding}
            className="text-slate-500 hover:text-slate-300 text-sm font-mono transition-colors"
          >
            ← Building
          </button>
          <span className="text-slate-700">|</span>
          <span className="text-lg font-bold text-white">🗄️ Archive</span>
          <span className="text-xs text-slate-500 font-mono hidden sm:block">
            — Knowledge Base Management
          </span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => void handleSeed()}
            disabled={seedLoading}
            className="text-xs px-3 py-1.5 rounded border border-amber-600 text-amber-400 hover:bg-amber-600 hover:text-white transition-all font-mono disabled:opacity-50"
          >
            {seedLoading ? "Seeding…" : "Seed Initial Data"}
          </button>
          <button
            onClick={() => { lockArchive(); goToBuilding(); }}
            className="text-xs px-3 py-1.5 rounded border border-slate-700 text-slate-400 hover:border-red-600 hover:text-red-400 transition-all font-mono"
          >
            🔒 Lock
          </button>
        </div>
      </div>

      {/* Seed result banner */}
      {seedResult && (
        <div className="mx-6 mt-4 px-4 py-2 bg-emerald-900/40 border border-emerald-700 rounded text-emerald-300 text-sm font-mono">
          {seedResult}
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-col lg:flex-row gap-6 p-6 flex-1 min-h-0">

        {/* Left column: Stats + Danger Zone */}
        <div className="lg:w-72 flex-shrink-0 flex flex-col gap-6">

          {/* Stats */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest font-mono">
                Collection Stats
              </h2>
              <button
                onClick={() => void fetchStats()}
                disabled={statsLoading}
                className="text-xs text-slate-600 hover:text-slate-400 font-mono transition-colors disabled:opacity-50"
              >
                {statsLoading ? "loading…" : "↻ refresh"}
              </button>
            </div>
            <div className="grid grid-cols-1 gap-3">
              {COLLECTIONS.map((col) => (
                <StatsCard
                  key={col.id}
                  collectionId={col.id}
                  stats={stats?.[col.id] ?? null}
                />
              ))}
            </div>
          </section>

          {/* Danger Zone */}
          <section>
            <h2 className="text-xs font-semibold text-red-600 uppercase tracking-widest font-mono mb-3">
              Danger Zone
            </h2>
            <div className="flex flex-col gap-2">
              {COLLECTIONS.map((col) => (
                <div key={col.id}>
                  {clearTarget === col.id ? (
                    <div className="bg-red-950 border border-red-700 rounded-lg p-3 flex flex-col gap-2">
                      <p className="text-xs text-red-300 font-mono">
                        Hapus semua dokumen di <strong>{col.label}</strong>?
                      </p>
                      <div className="flex gap-2">
                        <button
                          onClick={() => void handleClear(col.id)}
                          disabled={clearLoading}
                          className="flex-1 text-xs py-1.5 rounded bg-red-700 hover:bg-red-600 text-white font-mono transition-colors disabled:opacity-50"
                        >
                          {clearLoading ? "Deleting…" : "Konfirmasi Hapus"}
                        </button>
                        <button
                          onClick={() => setClearTarget(null)}
                          className="flex-1 text-xs py-1.5 rounded border border-slate-600 text-slate-400 hover:text-white font-mono transition-colors"
                        >
                          Batal
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => setClearTarget(col.id)}
                      className="w-full text-left text-xs px-3 py-2 rounded border border-slate-800 text-slate-600 hover:border-red-700 hover:text-red-400 font-mono transition-all"
                    >
                      Clear {col.label}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Right column: Add Document form */}
        <div className="flex-1 min-w-0">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest font-mono mb-4">
            Tambah Dokumen
          </h2>

          <form onSubmit={(e) => void handleSubmit(e)} className="flex flex-col gap-4">
            {/* Collection selector */}
            <div>
              <label className="block text-xs text-slate-500 font-mono mb-1.5">
                Collection
              </label>
              <select
                value={selectedCollection}
                onChange={(e) => setSelectedCollection(e.target.value as CollectionId)}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2.5 text-white text-sm font-mono outline-none focus:border-amber-500 transition-colors"
              >
                {COLLECTIONS.map((col) => (
                  <option key={col.id} value={col.id}>
                    {col.label} — {col.description}
                  </option>
                ))}
              </select>
            </div>

            {/* Content textarea */}
            <div>
              <label className="block text-xs text-slate-500 font-mono mb-1.5">
                Konten Dokumen <span className="text-red-500">*</span>
              </label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                required
                rows={10}
                placeholder={
                  selectedCollection === "sop_policies"
                    ? "Kebijakan kompensasi untuk kasus X: Jika kondisi Y terpenuhi, maka pelanggan berhak mendapatkan..."
                    : selectedCollection === "faq_patterns"
                    ? "Pola keluhan: Pelanggan melaporkan... Kata kunci: '...'. Tipe: ... Respons yang tepat: ..."
                    : selectedCollection === "product_catalog"
                    ? "Produk kategori X: Deskripsi, spesifikasi, kebijakan garansi..."
                    : "Isi konten dokumen..."
                }
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-white text-sm font-mono outline-none focus:border-amber-500 transition-colors resize-y placeholder:text-slate-600"
              />
            </div>

            {/* Metadata */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-slate-500 font-mono mb-1.5">
                  Category (opsional)
                </label>
                <input
                  type="text"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  placeholder="misal: compensation"
                  className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm font-mono outline-none focus:border-amber-500 transition-colors placeholder:text-slate-600"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-500 font-mono mb-1.5">
                  Source (opsional)
                </label>
                <input
                  type="text"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  placeholder="misal: sop-v3.pdf"
                  className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm font-mono outline-none focus:border-amber-500 transition-colors placeholder:text-slate-600"
                />
              </div>
            </div>

            {/* Submit result */}
            {submitResult && (
              <div
                className={`px-4 py-2 rounded text-sm font-mono ${
                  submitResult.ok
                    ? "bg-emerald-900/40 border border-emerald-700 text-emerald-300"
                    : "bg-red-950 border border-red-700 text-red-300"
                }`}
              >
                {submitResult.ok ? "✓" : "✗"} {submitResult.message}
              </div>
            )}

            <button
              type="submit"
              disabled={submitLoading || !content.trim()}
              className="self-start px-6 py-2.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {submitLoading ? "Uploading…" : "Submit Dokumen"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
