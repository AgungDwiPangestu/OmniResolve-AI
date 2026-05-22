"use client";

import { useState, useRef, useEffect } from "react";
import { useNavigationStore } from "@/stores/navigationStore";

export function ArchiveKeyPrompt(): React.ReactNode {
  const [key, setKey] = useState("");
  const [error, setError] = useState(false);
  const [shake, setShake] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const goToBuilding = useNavigationStore((s) => s.goToBuilding);
  const unlockArchive = useNavigationStore((s) => s.unlockArchive);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const validKey = process.env.NEXT_PUBLIC_ARCHIVE_KEY;
    if (!validKey || key === validKey) {
      unlockArchive();
    } else {
      setError(true);
      setShake(true);
      setKey("");
      setTimeout(() => setShake(false), 500);
    }
  };

  return (
    <div className="flex items-center justify-center h-full bg-slate-950">
      <div
        className={`w-full max-w-md mx-4 ${shake ? "animate-[shake_0.4s_ease-in-out]" : ""}`}
        style={
          shake
            ? { animation: "shake 0.4s ease-in-out" }
            : {}
        }
      >
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">🗄️</div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Archive Access
          </h1>
          <p className="text-sm text-slate-500 mt-2 font-mono">
            Qhomemart Knowledge Base Management
          </p>
        </div>

        {/* Key form */}
        <form
          onSubmit={handleSubmit}
          className="bg-slate-900 border border-slate-700 rounded-xl p-6 flex flex-col gap-4"
        >
          <div>
            <label
              htmlFor="archive-key"
              className="block text-xs text-slate-400 font-mono uppercase tracking-widest mb-2"
            >
              Admin Key
            </label>
            <input
              id="archive-key"
              ref={inputRef}
              type="password"
              value={key}
              onChange={(e) => {
                setKey(e.target.value);
                setError(false);
              }}
              placeholder="Enter admin key..."
              className={`w-full bg-slate-800 border rounded-lg px-4 py-3 text-white font-mono text-sm outline-none transition-colors placeholder:text-slate-600 ${
                error
                  ? "border-red-500 focus:border-red-400"
                  : "border-slate-600 focus:border-amber-500"
              }`}
            />
            {error && (
              <p className="text-red-400 text-xs mt-2 font-mono">
                Invalid key. Access denied.
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={!key.trim()}
            className="w-full py-3 rounded-lg font-semibold text-sm transition-all bg-amber-500 hover:bg-amber-400 text-slate-900 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Unlock Archive
          </button>
        </form>

        {/* Back link */}
        <div className="text-center mt-6">
          <button
            onClick={goToBuilding}
            className="text-slate-600 hover:text-slate-400 text-sm font-mono transition-colors"
          >
            ← Back to Building
          </button>
        </div>
      </div>

      <style>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          20% { transform: translateX(-8px); }
          40% { transform: translateX(8px); }
          60% { transform: translateX(-6px); }
          80% { transform: translateX(6px); }
        }
      `}</style>
    </div>
  );
}
