"use client";

import { useEffect, useState } from "react";
import { X, Check, AlertTriangle, User, ShoppingBag, FileText, CheckCircle2, ShieldAlert } from "lucide-react";

interface HitlSessionDetail {
  session_id: string;
  raw_input: string;
  customer_id: string | null;
  customer_name: string | null;
  order_id: string | null;
  complaint_type: string | null;
  sentiment_score: number | null;
  claim_valid: boolean | null;
  stock_status: string | null;
  audit_notes: string | null;
  decision_type: string | null;
  compensation_value_idr: number | null;
  requires_human_approval: boolean;
  chain_of_thought: string | null;
  actions_taken: string | null;
  status: string;
  created_at: string;
}

interface HitlSupervisorModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  onActionComplete: (message: string, success: boolean) => void;
}

export default function HitlSupervisorModal({
  isOpen,
  onClose,
  sessionId,
  onActionComplete,
}: HitlSupervisorModalProps) {
  const [detail, setDetail] = useState<HitlSessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<"approve" | "reject" | null>(null);

  useEffect(() => {
    if (!isOpen || !sessionId) return;

    const fetchDetail = async () => {
      setLoading(true);
      setError(null);
      try {
        const apiBase = `http://${window.location.hostname}:8000`;
        const res = await fetch(`${apiBase}/api/v1/complaints/detail/${sessionId}`);
        if (!res.ok) {
          throw new Error("Failed to load HITL session details from backend.");
        }
        const data = await res.json();
        setDetail(data);
      } catch (err: any) {
        setError(err.message || "An unexpected error occurred.");
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [isOpen, sessionId]);

  const handleAction = async (action: "approve" | "reject") => {
    if (!sessionId) return;
    setSubmitting(action);
    try {
      const apiBase = `http://${window.location.hostname}:8000`;
      const res = await fetch(`${apiBase}/api/v1/complaints/${action}/${sessionId}`, {
        method: "POST",
      });

      if (!res.ok) {
        throw new Error(`Failed to ${action} the complaint.`);
      }

      const data = await res.json();
      onActionComplete(data.message || `Successfully ${action}d the decision.`, true);
      onClose();
    } catch (err: any) {
      onActionComplete(err.message || `Failed to complete ${action} action.`, false);
    } finally {
      setSubmitting(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-amber-500/30 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/50 flex-shrink-0">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10 text-amber-500">
              <ShieldAlert size={22} className="animate-pulse" />
            </span>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                Qhome HITL Supervisor Portal
              </h2>
              <p className="text-xs text-slate-400 font-mono">Session: {sessionId}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-6 text-slate-300 text-sm leading-relaxed overflow-y-auto flex-1 min-h-0 space-y-6">
          {loading ? (
            <div className="space-y-4 py-8">
              <div className="h-4 bg-slate-800 rounded w-1/3 animate-pulse"></div>
              <div className="h-24 bg-slate-800 rounded animate-pulse"></div>
              <div className="h-4 bg-slate-800 rounded w-1/2 animate-pulse"></div>
              <div className="h-20 bg-slate-800 rounded animate-pulse"></div>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center text-center p-6 border border-rose-500/20 bg-rose-500/5 rounded-xl gap-2">
              <AlertTriangle size={36} className="text-rose-500" />
              <h3 className="font-bold text-white">Failed to Load Details</h3>
              <p className="text-xs text-slate-400">{error}</p>
            </div>
          ) : detail ? (
            <>
              {/* Alert Ribbon */}
              <div className="flex items-start gap-3 p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                <AlertTriangle className="text-amber-500 shrink-0 mt-0.5" size={18} />
                <div className="space-y-1">
                  <p className="text-xs font-bold text-amber-400 uppercase tracking-wider font-mono">
                    High Value Compensation Requires Action
                  </p>
                  <p className="text-xs text-slate-300">
                    The autonomous agent pipeline proposed a compensation of{" "}
                    <span className="font-bold text-white">
                      Rp {detail.compensation_value_idr?.toLocaleString("id-ID") || "0"}
                    </span>{" "}
                    which exceeds the maximum auto-release limit of Rp 1,000,000. Please review the details below.
                  </p>
                </div>
              </div>

              {/* Customer & Order Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-3">
                  <h4 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1.5 font-mono">
                    <User size={14} className="text-indigo-400" /> Customer Information
                  </h4>
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-white">
                      {detail.customer_name || "Unknown"}
                    </p>
                    <p className="text-xs text-slate-400 font-mono">ID: {detail.customer_id || "N/A"}</p>
                    <div className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-xs font-mono">
                      Sentiment:{" "}
                      <span className={detail.sentiment_score && detail.sentiment_score < 0.3 ? "text-rose-400 font-bold" : "text-emerald-400"}>
                        {detail.sentiment_score ? detail.sentiment_score.toFixed(2) : "N/A"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-3">
                  <h4 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1.5 font-mono">
                    <ShoppingBag size={14} className="text-sky-400" /> Order Information
                  </h4>
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-white">
                      Order ID: <span className="font-mono text-purple-400">{detail.order_id || "N/A"}</span>
                    </p>
                    <p className="text-xs text-slate-400">Complaint Type: {detail.complaint_type || "N/A"}</p>
                    <div className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-xs font-mono">
                      Stock Status:{" "}
                      <span className={detail.stock_status === "Available" ? "text-emerald-400" : "text-rose-400 font-semibold"}>
                        {detail.stock_status || "N/A"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Raw Customer Message */}
              <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1.5 font-mono">
                  <FileText size={14} className="text-amber-400" /> Raw Complaint Message
                </h4>
                <p className="text-xs italic text-slate-300 font-sans border-l-2 border-slate-700 pl-3 leading-relaxed">
                  "{detail.raw_input}"
                </p>
              </div>

              {/* Verification & Suggested Action */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-3">
                  <h4 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1.5 font-mono">
                    <CheckCircle2 size={14} className="text-emerald-400" /> Claims Audit
                  </h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                      <span className="text-slate-400">Claim Validity</span>
                      <span className={`font-bold ${detail.claim_valid ? "text-emerald-400" : "text-rose-400"}`}>
                        {detail.claim_valid ? "VALID ✅" : "INVALID ❌"}
                      </span>
                    </div>
                    <div className="space-y-1">
                      <span className="text-slate-400">Audit Notes:</span>
                      <p className="text-[11px] text-slate-300 bg-slate-900 p-2 rounded border border-slate-800 font-mono">
                        {detail.audit_notes || "No notes from Logistics Auditor."}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-3">
                  <h4 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1.5 font-mono">
                    <ShieldAlert size={14} className="text-orange-400" /> Proposed Compensation
                  </h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                      <span className="text-slate-400">Proposed Action</span>
                      <span className="font-bold text-white uppercase px-2 py-0.5 bg-amber-500/20 border border-amber-500/30 rounded">
                        {detail.decision_type || "N/A"}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                      <span className="text-slate-400">Suggested Value</span>
                      <span className="font-bold text-emerald-400 text-sm">
                        Rp {detail.compensation_value_idr?.toLocaleString("id-ID") || "0"}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1">
                      <span className="text-slate-400">Auto-Escalated</span>
                      <span className="text-amber-400 font-bold">YES</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Chain of Thought / AI reasoning */}
              <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1.5 font-mono">
                  🧠 Agent Reasoning (Strategic Negotiator CoT)
                </h4>
                <p className="text-[11px] text-slate-300 font-mono bg-slate-955 p-3 rounded-lg border border-slate-800 max-h-32 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                  {detail.chain_of_thought || "No reasoning chain provided."}
                </p>
              </div>
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-900/50 flex-shrink-0">
          <div className="text-xs text-slate-400">
            Status: <span className="font-bold text-amber-500 font-mono uppercase">{detail?.status || "Unknown"}</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => handleAction("reject")}
              disabled={submitting !== null || loading}
              className="inline-flex items-center gap-2 px-4 py-2 border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 disabled:opacity-50 text-rose-400 hover:text-rose-300 text-sm font-bold rounded-xl transition-all"
            >
              {submitting === "reject" ? "Rejecting..." : "Reject & Cancel"}
            </button>
            <button
              onClick={() => handleAction("approve")}
              disabled={submitting !== null || loading}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 text-white text-sm font-bold rounded-xl transition-all shadow-lg shadow-emerald-950/30 hover:scale-[1.02]"
            >
              <Check size={16} />
              {submitting === "approve" ? "Approving..." : "Approve & Process ERP"}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
