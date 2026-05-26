"use client";

import { useState, useCallback, useRef, DragEvent, ChangeEvent } from "react";
import { useNavigationStore } from "@/stores/navigationStore";

// ============================================================================
// CONSTANTS
// ============================================================================

const COLLECTIONS = [
  { id: "sop_policies", label: "SOP & Kebijakan", description: "Aturan bisnis dan SOP Qhomemart" },
  { id: "faq_patterns", label: "Pola FAQ", description: "Pola keluhan umum dan respons ideal" },
  { id: "product_catalog", label: "Katalog Produk", description: "Info produk, kategori, garansi" },
  { id: "resolved_cases", label: "Kasus Selesai", description: "Diisi otomatis oleh feedback loop" },
] as const;

type CollectionId = (typeof COLLECTIONS)[number]["id"];

const ACCEPTED_EXTS = [".pdf", ".docx", ".doc", ".md", ".txt"];
const ACCEPTED_MIME = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/msword",
  "text/markdown",
  "text/plain",
];

function getApiUrl(): string {
  return (process.env.NEXT_PUBLIC_OMNI_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
}

function getFileIcon(name: string): string {
  const ext = name.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "📄";
  if (ext === "docx" || ext === "doc") return "📝";
  if (ext === "md") return "📋";
  return "📃";
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ============================================================================
// MAIN ARCHIVE VIEW — Full-screen upload overlay
// ============================================================================

export function ArchiveView(): React.ReactNode {
  const goToBuilding = useNavigationStore((s) => s.goToBuilding);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [collection, setCollection] = useState<CollectionId>("sop_policies");
  const [category, setCategory] = useState("");
  const [source, setSource] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // -------------------------------------------------------------------------
  // File selection helpers
  // -------------------------------------------------------------------------

  const acceptFile = useCallback((file: File) => {
    const ext = "." + (file.name.split(".").pop()?.toLowerCase() ?? "");
    if (!ACCEPTED_EXTS.includes(ext) && !ACCEPTED_MIME.includes(file.type)) {
      setResult({ ok: false, message: `Format '${ext}' tidak didukung. Gunakan: PDF, DOCX, MD, atau TXT.` });
      return;
    }
    setSelectedFile(file);
    setResult(null);
    // auto-fill source from filename
    if (!source) setSource(file.name);
  }, [source]);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) acceptFile(file);
  };

  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) acceptFile(file);
  };

  // -------------------------------------------------------------------------
  // Upload
  // -------------------------------------------------------------------------

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setResult(null);

    const form = new FormData();
    form.append("file", selectedFile);
    form.append("collection", collection);
    if (category.trim()) form.append("category", category.trim());
    if (source.trim()) form.append("source", source.trim());

    try {
      const res = await fetch(`${getApiUrl()}/api/v1/admin/knowledge/upload`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const err = (await res.json()) as { detail?: string };
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }
      const data = (await res.json()) as { message: string };
      setResult({ ok: true, message: data.message });
      setSelectedFile(null);
      setCategory("");
      setSource("");
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (e) {
      setResult({ ok: false, message: `Upload gagal: ${String(e)}` });
    } finally {
      setUploading(false);
    }
  };

  // -------------------------------------------------------------------------
  // RENDER
  // -------------------------------------------------------------------------

  return (
    <div className="fixed inset-0 z-50 bg-slate-950 flex flex-col">

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 flex-shrink-0">
        <button
          onClick={goToBuilding}
          className="flex items-center gap-2 text-slate-400 hover:text-white text-sm font-mono transition-colors group"
        >
          <span className="group-hover:-translate-x-0.5 transition-transform">←</span>
          <span>Pilih Lantai</span>
        </button>
        <div className="flex items-center gap-2">
          <span className="text-lg">🗄️</span>
          <span className="text-white font-bold">Archive</span>
          <span className="text-slate-600 font-mono text-xs hidden sm:block">— RAG Document Upload</span>
        </div>
        {/* spacer untuk balance */}
        <div className="w-28" />
      </div>

      {/* ── Body ── */}
      <div className="flex-1 overflow-y-auto flex items-start justify-center p-6 sm:p-10">
        <div className="w-full max-w-2xl flex flex-col gap-6">

          {/* Collection selector */}
          <div>
            <label className="block text-xs text-slate-500 font-mono uppercase tracking-widest mb-2">
              Collection Tujuan
            </label>
            <select
              value={collection}
              onChange={(e) => setCollection(e.target.value as CollectionId)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white text-sm font-mono outline-none focus:border-amber-500 transition-colors"
            >
              {COLLECTIONS.map((col) => (
                <option key={col.id} value={col.id}>
                  {col.label} — {col.description}
                </option>
              ))}
            </select>
          </div>

          {/* Drop zone */}
          <div>
            <label className="block text-xs text-slate-500 font-mono uppercase tracking-widest mb-2">
              File Dokumen <span className="text-red-500">*</span>
            </label>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`
                relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed
                px-6 py-12 cursor-pointer transition-all select-none
                ${isDragging
                  ? "border-amber-400 bg-amber-900/20"
                  : selectedFile
                    ? "border-emerald-600 bg-emerald-900/10 hover:bg-emerald-900/20"
                    : "border-slate-700 bg-slate-900 hover:border-slate-500 hover:bg-slate-800/50"
                }
              `}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_EXTS.join(",")}
                className="hidden"
                onChange={handleFileInput}
              />

              {selectedFile ? (
                <>
                  <span className="text-4xl">{getFileIcon(selectedFile.name)}</span>
                  <div className="text-center">
                    <p className="text-white font-mono text-sm font-semibold">{selectedFile.name}</p>
                    <p className="text-slate-500 font-mono text-xs mt-0.5">{formatBytes(selectedFile.size)}</p>
                  </div>
                  <p className="text-emerald-400 text-xs font-mono">Klik untuk ganti file</p>
                </>
              ) : (
                <>
                  <span className="text-5xl opacity-40">📂</span>
                  <div className="text-center">
                    <p className="text-slate-300 font-mono text-sm">
                      {isDragging ? "Lepas file di sini..." : "Drag & drop file, atau klik untuk browse"}
                    </p>
                    <p className="text-slate-600 font-mono text-xs mt-1">
                      PDF · DOCX · Markdown · TXT
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-500 font-mono uppercase tracking-widest mb-2">
                Category (opsional)
              </label>
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="misal: compensation"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white text-sm font-mono outline-none focus:border-amber-500 transition-colors placeholder:text-slate-600"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 font-mono uppercase tracking-widest mb-2">
                Source (opsional)
              </label>
              <input
                type="text"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder="misal: sop-v3.pdf"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white text-sm font-mono outline-none focus:border-amber-500 transition-colors placeholder:text-slate-600"
              />
            </div>
          </div>

          {/* Result */}
          {result && (
            <div
              className={`px-4 py-3 rounded-lg text-sm font-mono border ${
                result.ok
                  ? "bg-emerald-900/30 border-emerald-700 text-emerald-300"
                  : "bg-red-950/50 border-red-700 text-red-300"
              }`}
            >
              {result.ok ? "✓ " : "✗ "}
              {result.message}
            </div>
          )}

          {/* Upload button */}
          <button
            onClick={() => void handleUpload()}
            disabled={!selectedFile || uploading}
            className="w-full py-3.5 rounded-xl bg-amber-500 hover:bg-amber-400 active:scale-[0.98] text-slate-900 font-bold text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100"
          >
            {uploading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="inline-block w-3.5 h-3.5 border-2 border-slate-900/40 border-t-slate-900 rounded-full animate-spin" />
                Mengupload…
              </span>
            ) : (
              "Upload Dokumen"
            )}
          </button>

          <p className="text-center text-slate-700 text-xs font-mono">
            Dokumen akan diparse dan disimpan ke RAG vector store
          </p>

        </div>
      </div>
    </div>
  );
}
