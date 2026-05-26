"use client";

import { useState, useEffect, useCallback } from "react";
import { useNavigationStore } from "@/stores/navigationStore";

function getApiUrl(): string {
  return (process.env.NEXT_PUBLIC_OMNI_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
}

interface DayCount { date: string; count: number; }
interface DecisionBreakdown { decision_type: string; count: number; total_compensation_idr: number; }
interface DashboardMetrics {
  total_today: number;
  resolved_today: number;
  rejected_today: number;
  pending_approval: number;
  total_compensation_idr: number;
  compensation_7days_idr: number;
  money_saved_idr: number;
  by_decision_type: DecisionBreakdown[];
  last_7_days: DayCount[];
}

function formatRp(v: number) {
  if (v >= 1_000_000) return `Rp ${(v / 1_000_000).toFixed(1)}jt`;
  if (v >= 1_000) return `Rp ${(v / 1_000).toFixed(0)}rb`;
  return `Rp ${v.toLocaleString("id-ID")}`;
}

function formatRpFull(v: number) {
  return "Rp " + v.toLocaleString("id-ID");
}

const DECISION_LABELS: Record<string, { label: string; color: string; bg: string }> = {
  replacement: { label: "Penggantian",  color: "text-amber-300",  bg: "bg-amber-900/40 border-amber-700" },
  voucher:     { label: "Voucher",      color: "text-blue-300",   bg: "bg-blue-900/40 border-blue-700" },
  refund:      { label: "Refund",       color: "text-purple-300", bg: "bg-purple-900/40 border-purple-700" },
  reject:      { label: "Ditolak",      color: "text-slate-400",  bg: "bg-slate-800 border-slate-700" },
  multi_choice:{ label: "Multi-Opsi",   color: "text-cyan-300",   bg: "bg-cyan-900/40 border-cyan-700" },
};

export function BossRoomView(): React.ReactNode {
  const goToBuilding = useNavigationStore((s) => s.goToBuilding);
  const [data, setData] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/admin/dashboard`);
      if (res.ok) {
        setData(await res.json() as DashboardMetrics);
        setLastUpdated(new Date().toLocaleTimeString("id-ID"));
      }
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void fetchData(); }, [fetchData]);
  // Auto-refresh tiap 30 detik
  useEffect(() => {
    const t = setInterval(() => { void fetchData(); }, 30_000);
    return () => clearInterval(t);
  }, [fetchData]);

  const metrics = [
    { label: "Keluhan Hari Ini", value: data?.total_today ?? 0, icon: "📩", color: "text-indigo-300", border: "border-indigo-800 bg-indigo-900/20" },
    { label: "Diselesaikan",     value: data?.resolved_today ?? 0, icon: "✅", color: "text-green-300", border: "border-green-800 bg-green-900/20" },
    { label: "Ditolak",          value: data?.rejected_today ?? 0, icon: "❌", color: "text-slate-400", border: "border-slate-700 bg-slate-800/40" },
    { label: "Perlu Approval",   value: data?.pending_approval ?? 0, icon: "⚠️", color: "text-amber-300", border: "border-amber-800 bg-amber-900/20" },
    { label: "Total Kompensasi (All Time)", value: formatRp(data?.total_compensation_idr ?? 0), icon: "💸", color: "text-purple-300", border: "border-purple-800 bg-purple-900/20", wide: true },
    { label: "Penghematan Estimasi (Reject)", value: formatRp(data?.money_saved_idr ?? 0), icon: "💰", color: "text-emerald-300", border: "border-emerald-800 bg-emerald-900/20", wide: true },
  ];

  // Bar chart dari last_7_days
  const days = data?.last_7_days ?? [];
  const maxCount = Math.max(1, ...days.map((d) => d.count));

  return (
    <div className="flex flex-col h-full bg-slate-950 text-white overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 flex-shrink-0">
        <button onClick={goToBuilding} className="flex items-center gap-2 text-slate-400 hover:text-white text-sm font-mono transition-colors group">
          <span className="group-hover:-translate-x-0.5 transition-transform">←</span>
          <span>Pilih Lantai</span>
        </button>
        <div className="flex items-center gap-2">
          <span className="text-lg">📊</span>
          <span className="text-white font-bold">Boss Room</span>
          <span className="text-slate-600 font-mono text-xs hidden sm:block">— Operations Dashboard</span>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdated && <span className="text-xs text-slate-600 font-mono hidden sm:block">Updated {lastUpdated}</span>}
          <button onClick={() => void fetchData()} className="text-xs text-slate-500 hover:text-indigo-400 font-mono transition-colors">
            ↻ Refresh
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-8">

        {/* Metric cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {metrics.slice(0, 4).map((m) => (
            <div key={m.label} className={`rounded-xl border p-5 ${m.border}`}>
              <div className="flex items-start justify-between">
                <span className="text-2xl">{m.icon}</span>
              </div>
              <p className={`text-3xl font-bold mt-3 ${m.color}`}>
                {loading ? "—" : typeof m.value === "number" ? m.value : m.value}
              </p>
              <p className="text-xs text-slate-500 font-mono mt-1">{m.label}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {metrics.slice(4).map((m) => (
            <div key={m.label} className={`rounded-xl border p-5 ${m.border}`}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xl">{m.icon}</span>
                <p className="text-xs text-slate-500 font-mono">{m.label}</p>
              </div>
              <p className={`text-2xl font-bold ${m.color}`}>
                {loading ? "—" : m.value}
              </p>
              {!loading && data && m.label.includes("Kompensasi") && (
                <p className="text-xs text-slate-600 font-mono mt-1">
                  7 hari: {formatRpFull(data.compensation_7days_idr)}
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Bar chart: 7 hari terakhir */}
        <section>
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest font-mono mb-4">
            Keluhan 7 Hari Terakhir
          </h2>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            {loading ? (
              <p className="text-slate-600 font-mono text-sm text-center py-4">Loading...</p>
            ) : days.length === 0 ? (
              <p className="text-slate-600 font-mono text-sm text-center py-4">Belum ada data</p>
            ) : (
              <div className="flex items-end gap-3 h-32">
                {days.map((d) => (
                  <div key={d.date} className="flex flex-col items-center gap-1 flex-1">
                    <span className="text-xs text-indigo-300 font-bold font-mono">{d.count}</span>
                    <div
                      className="w-full bg-indigo-500/70 rounded-t transition-all"
                      style={{ height: `${Math.max(4, (d.count / maxCount) * 100)}px` }}
                    />
                    <span className="text-[10px] text-slate-600 font-mono">
                      {d.date.slice(5)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Breakdown by decision type */}
        <section>
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest font-mono mb-4">
            Breakdown Keputusan (All Time)
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {loading ? (
              <p className="text-slate-600 font-mono text-sm">Loading...</p>
            ) : (data?.by_decision_type ?? []).map((b) => {
              const meta = DECISION_LABELS[b.decision_type] ?? { label: b.decision_type, color: "text-slate-300", bg: "bg-slate-800 border-slate-700" };
              return (
                <div key={b.decision_type} className={`rounded-xl border p-4 ${meta.bg}`}>
                  <p className={`text-xs font-mono uppercase tracking-widest ${meta.color}`}>{meta.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">{b.count}</p>
                  <p className="text-xs text-slate-600 font-mono mt-1">Total: {formatRpFull(b.total_compensation_idr)}</p>
                </div>
              );
            })}
          </div>
        </section>

      </div>
    </div>
  );
}
