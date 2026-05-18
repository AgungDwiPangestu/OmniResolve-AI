/**
 * Claude Office Visualizer - Main Page
 *
 * Uses the unified Zustand store, XState machines, and OfficeGame component.
 * Layout and logic are delegated to extracted components and custom hooks.
 *
 * Navigation modes:
 * - "single" (default): the original flat layout with sidebar + canvas + sidebar
 * - "building": cross-section building view (when user configures floors)
 * - "floor": floor-level view wrapping the office canvas
 */

"use client";

import dynamic from "next/dynamic";
import { useState, useEffect, useCallback, useRef } from "react";
import { useWebSocketEvents } from "@/hooks/useWebSocketEvents";
import { useSessions } from "@/hooks/useSessions";
import { useSessionSwitch } from "@/hooks/useSessionSwitch";
import { useFloorConfig } from "@/hooks/useFloorConfig";
import {
  useGameStore,
  selectIsConnected,
  selectDebugMode,
  selectAgents,
  selectBoss,
} from "@/stores/gameStore";
import { useNavigationStore } from "@/stores/navigationStore";
import { useTourStore } from "@/stores/tourStore";
import { useShallow } from "zustand/react/shallow";
import { Menu, X, Check, AlertTriangle, User, ShoppingBag, FileText, CheckCircle2, ShieldAlert } from "lucide-react";
import { SessionSidebar } from "@/components/layout/SessionSidebar";
import { MobileDrawer } from "@/components/layout/MobileDrawer";
import { MobileAgentActivity } from "@/components/layout/MobileAgentActivity";
import { RightSidebar } from "@/components/layout/RightSidebar";
import { HeaderControls } from "@/components/layout/HeaderControls";
import {
  StatusToast,
  type StatusMessage,
} from "@/components/layout/StatusToast";
import Modal from "@/components/overlay/Modal";
import SettingsModal from "@/components/overlay/SettingsModal";
import { Breadcrumb } from "@/components/navigation/Breadcrumb";
import { ViewTransition } from "@/components/navigation/ViewTransition";
import { BuildingView } from "@/components/views/BuildingView";
import { FloorView } from "@/components/views/FloorView";
import { TourOverlay } from "@/components/tour/TourOverlay";
import CommandBar from "@/components/attention/CommandBar";
import AttentionToasts from "@/components/attention/AttentionToasts";
import AgentPopup from "@/components/attention/AgentPopup";
import { useAttentionStore } from "@/stores/attentionStore";
import { usePreferencesStore } from "@/stores/preferencesStore";
import { useTranslation } from "@/hooks/useTranslation";
import type { Session } from "@/hooks/useSessions";

// ============================================================================
// DYNAMIC IMPORT
// ============================================================================

function LoadingFallback() {
  const { t } = useTranslation();
  return (
    <div className="w-full h-full bg-slate-900 animate-pulse flex items-center justify-center text-white font-mono text-center">
      {t("app.initializingSystems")}
    </div>
  );
}

const OfficeGame = dynamic(
  () =>
    import("@/components/game/OfficeGame").then((m) => ({
      default: m.OfficeGame,
    })),
  {
    ssr: false,
    loading: () => <LoadingFallback />,
  },
);

// ============================================================================
// PAGE COMPONENT
// ============================================================================

export default function V2TestPage(): React.ReactNode {
  // ------------------------------------------------------------------
  // i18n
  // ------------------------------------------------------------------
  const { t, language } = useTranslation();

  // ------------------------------------------------------------------
  // UI-only state
  // ------------------------------------------------------------------
  const [isClearModalOpen, setIsClearModalOpen] = useState(false);
  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [settingsInitialTab, setSettingsInitialTab] = useState<
    "general" | "building"
  >("general");
  const [statusMessage, setStatusMessage] = useState<StatusMessage | null>(
    null,
  );
  const [leftSidebarCollapsed, setLeftSidebarCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [aiSummaryEnabled, setAiSummaryEnabled] = useState<boolean | null>(
    null,
  );

  // Session pending delete drives the delete-confirmation modal
  const [sessionPendingDelete, setSessionPendingDelete] =
    useState<Session | null>(null);

  // ------------------------------------------------------------------
  // Status toast helper (stable reference via useCallback)
  // ------------------------------------------------------------------
  const showStatus = useCallback(
    (text: string, type: "info" | "error" | "success" = "info") => {
      setStatusMessage({ text, type });
      setTimeout(() => setStatusMessage(null), 3000);
    },
    [],
  );

  // ------------------------------------------------------------------
  // Session management hooks
  // ------------------------------------------------------------------
  const { sessions, sessionsLoading, sessionId, setSessionId, fetchSessions } =
    useSessions(showStatus);

  const {
    handleSessionSelect,
    handleDeleteSession,
    handleClearDB,
    handleSimulate,
    handleReset,
    handleRenameSession,
  } = useSessionSwitch({ sessionId, setSessionId, fetchSessions, showStatus });

  // HITL Supervisor State Variables
  const [hitlSessionId, setHitlSessionId] = useState<string | null>(null);
  const [hitlDetail, setHitlDetail] = useState<any | null>(null);
  const [hitlLoading, setHitlLoading] = useState(false);
  const [hitlActionLoading, setHitlActionLoading] = useState(false);
  const dismissedSessionsRef = useRef<Set<string>>(new Set());

  // Parse query params for ?hitl_session=...
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const hitlParam = params.get("hitl_session");
      if (hitlParam) {
        setHitlSessionId(hitlParam);
        
        // Remove param from URL cleanly without page reload
        const newUrl = window.location.pathname + window.location.search.replace(/[\?&]hitl_session=[^&]+/, "").replace(/^&/, "?");
        window.history.replaceState({}, document.title, newUrl);
      }
    }
  }, []);

  // Poll for pending HITL tasks
  useEffect(() => {
    const pollPendingHitl = async () => {
      if (hitlSessionId) return;

      try {
        const apiBase = `http://${window.location.hostname}:8000`;
        const res = await fetch(`${apiBase}/api/v1/complaints/logs`);
        if (res.ok) {
          const logs = await res.json();
          const pending = logs.find((l: any) => l.status === "pending_hitl");
          if (pending && !dismissedSessionsRef.current.has(pending.session_id)) {
            setHitlSessionId(pending.session_id);
          }
        }
      } catch (err) {
        // Silently ignore
      }
    };

    pollPendingHitl();
    const interval = setInterval(pollPendingHitl, 4000);
    return () => clearInterval(interval);
  }, [hitlSessionId]);

  // Fetch HITL details when sessionId changes
  useEffect(() => {
    if (!hitlSessionId) {
      setHitlDetail(null);
      return;
    }

    const fetchHitlDetail = async () => {
      setHitlLoading(true);
      try {
        const apiBase = `http://${window.location.hostname}:8000`;
        const res = await fetch(`${apiBase}/api/v1/complaints/detail/${hitlSessionId}`);
        if (res.ok) {
          const data = await res.json();
          setHitlDetail(data);
        } else {
          showStatus("Gagal memuat detail keluhan HITL.", "error");
        }
      } catch (err) {
        showStatus("Error memuat detail keluhan HITL.", "error");
      } finally {
        setHitlLoading(false);
      }
    };

    fetchHitlDetail();
  }, [hitlSessionId, showStatus]);

  // Approve / Reject handlers
  const handleHitlAction = async (action: "approve" | "reject") => {
    if (!hitlSessionId) return;
    setHitlActionLoading(true);
    try {
      const apiBase = `http://${window.location.hostname}:8000`;
      const res = await fetch(`${apiBase}/api/v1/complaints/${action}/${hitlSessionId}`, {
        method: "POST",
      });

      if (res.ok) {
        const data = await res.json();
        showStatus(data.message || `Keputusan keluhan telah di-${action}.`, "success");
        setHitlDetail((prev: any) => prev ? { ...prev, status: action === "approve" ? "approved" : "rejected" } : null);
        
        setTimeout(() => {
          dismissedSessionsRef.current.add(hitlSessionId);
          setHitlSessionId(null);
        }, 1500);
      } else {
        showStatus(`Gagal memproses tindakan ${action}.`, "error");
      }
    } catch (err) {
      showStatus(`Terjadi kesalahan saat memproses tindakan ${action}.`, "error");
    } finally {
      setHitlActionLoading(false);
    }
  };

  // ------------------------------------------------------------------
  // Store subscriptions
  // ------------------------------------------------------------------
  const isConnected = useGameStore(selectIsConnected);
  const debugMode = useGameStore(selectDebugMode);
  const agents = useGameStore(useShallow(selectAgents));
  const boss = useGameStore(selectBoss);
  const loadPersistedDebugSettings = useGameStore(
    (state) => state.loadPersistedDebugSettings,
  );
  const loadPreferences = usePreferencesStore((s) => s.loadPreferences);

  // Navigation store
  const view = useNavigationStore((s) => s.view);

  // ------------------------------------------------------------------
  // Floor config + tour initialization
  // ------------------------------------------------------------------
  useFloorConfig();

  // Watch for edit-building requests from BuildingView
  const consumeEditBuilding = useNavigationStore((s) => s.consumeEditBuilding);
  useEffect(() => {
    const interval = setInterval(() => {
      if (consumeEditBuilding()) {
        setSettingsInitialTab("building");
        setIsSettingsModalOpen(true);
      }
    }, 100);
    return () => clearInterval(interval);
  }, [consumeEditBuilding]);

  const loadTourSeen = useTourStore((s) => s.loadTourSeen);
  useEffect(() => {
    loadTourSeen();
  }, [loadTourSeen]);

  // ------------------------------------------------------------------
  // WebSocket connection — reconnects when sessionId changes
  // ------------------------------------------------------------------
  useWebSocketEvents({ sessionId });

  // ------------------------------------------------------------------
  // One-time initialization effects
  // ------------------------------------------------------------------
  useEffect(() => {
    fetch("/api/v1/status")
      .then((res) => res.json())
      .then((data: { aiSummaryEnabled: boolean }) =>
        setAiSummaryEnabled(data.aiSummaryEnabled),
      )
      .catch(() => setAiSummaryEnabled(false));
  }, []);

  useEffect(() => {
    loadPersistedDebugSettings();
  }, [loadPersistedDebugSettings]);

  useEffect(() => {
    loadPreferences();
  }, [loadPreferences]);

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  // ------------------------------------------------------------------
  // Mobile breakpoint detection
  // ------------------------------------------------------------------
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // ------------------------------------------------------------------
  // Cmd+K / Ctrl+K command bar toggle
  // ------------------------------------------------------------------
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (document.querySelector("[role='dialog'][aria-modal='true']")) return;
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        const prefs = usePreferencesStore.getState();
        if (!prefs.commandBarEnabled) return;
        const { isCommandBarOpen, closeCommandBar, openCommandBar } =
          useAttentionStore.getState();
        if (isCommandBarOpen) {
          closeCommandBar();
        } else {
          openCommandBar();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // ------------------------------------------------------------------
  // Derived handlers
  // ------------------------------------------------------------------
  const handleToggleDebug = () =>
    useGameStore.getState().setDebugMode(!debugMode);

  const handleConfirmClearDB = async () => {
    setIsClearModalOpen(false);
    await handleClearDB();
  };

  const handleConfirmDeleteSession = async () => {
    if (!sessionPendingDelete) return;
    const pending = sessionPendingDelete;
    setSessionPendingDelete(null);
    await handleDeleteSession(pending);
  };

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------
  return (
    <main className="flex h-screen flex-col bg-neutral-950 p-2 overflow-hidden relative">
      {/* ----------------------------------------------------------------
          Modals
      ---------------------------------------------------------------- */}
      <Modal
        isOpen={isClearModalOpen}
        onClose={() => setIsClearModalOpen(false)}
        title={t("modal.confirmDbWipe")}
        footer={
          <>
            <button
              onClick={() => setIsClearModalOpen(false)}
              className="px-4 py-2 text-slate-400 hover:text-white text-sm font-bold transition-colors"
            >
              {t("modal.cancel")}
            </button>
            <button
              onClick={handleConfirmClearDB}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-sm font-bold rounded-lg transition-colors shadow-lg shadow-rose-900/20"
            >
              {t("modal.wipeAllData")}
            </button>
          </>
        }
      >
        <p>{t("modal.wipeWarning")}</p>
      </Modal>

      <Modal
        isOpen={isHelpModalOpen}
        onClose={() => setIsHelpModalOpen(false)}
        title={t("modal.keyboardShortcuts")}
        footer={
          <button
            onClick={() => setIsHelpModalOpen(false)}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm font-bold rounded-lg transition-colors"
          >
            {t("modal.close")}
          </button>
        }
      >
        <div className="space-y-3 font-mono text-sm">
          <div className="flex justify-between items-center py-2 border-b border-slate-700">
            <kbd className="px-2 py-1 bg-slate-800 rounded text-white font-bold">
              D
            </kbd>
            <span className="text-slate-300">{t("modal.toggleDebug")}</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-slate-700">
            <kbd className="px-2 py-1 bg-slate-800 rounded text-white font-bold">
              P
            </kbd>
            <span className="text-slate-300">{t("modal.showAgentPaths")}</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-slate-700">
            <kbd className="px-2 py-1 bg-slate-800 rounded text-white font-bold">
              Q
            </kbd>
            <span className="text-slate-300">{t("modal.showQueueSlots")}</span>
          </div>
          <div className="flex justify-between items-center py-2">
            <kbd className="px-2 py-1 bg-slate-800 rounded text-white font-bold">
              L
            </kbd>
            <span className="text-slate-300">{t("modal.showPhaseLabels")}</span>
          </div>
        </div>
      </Modal>

      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
        initialTab={settingsInitialTab}
      />

      <Modal
        isOpen={sessionPendingDelete !== null}
        onClose={() => setSessionPendingDelete(null)}
        title={t("modal.deleteSession")}
        footer={
          <>
            <button
              onClick={() => setSessionPendingDelete(null)}
              className="px-4 py-2 text-slate-400 hover:text-white text-sm font-bold transition-colors"
            >
              {t("modal.cancel")}
            </button>
            <button
              onClick={handleConfirmDeleteSession}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-sm font-bold rounded-lg transition-colors shadow-lg shadow-rose-900/20"
            >
              {t("modal.delete")}
            </button>
          </>
        }
      >
        <p>
          {t("modal.deleteSessionConfirm")}{" "}
          <span className="font-mono text-purple-400">
            {sessionPendingDelete?.projectName ||
              sessionPendingDelete?.id.slice(0, 8)}
          </span>
          ?
        </p>
        <p className="text-slate-400 text-sm mt-2">
          {t("modal.deleteSessionWarning")}{" "}
          {sessionPendingDelete?.eventCount ?? 0} {t("modal.events")}.{" "}
          {t("modal.cannotBeUndone")}
        </p>
      </Modal>

      {/* ----------------------------------------------------------------
          Header
      ---------------------------------------------------------------- */}
      <header className="flex justify-between items-center mb-2 px-1 relative h-12">
        <div className="flex items-center gap-3">
          {isMobile && (
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label={mobileMenuOpen ? t("modal.close") : t("mobile.menu")}
              aria-expanded={mobileMenuOpen}
              className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-white transition-colors"
            >
              {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          )}
          <h1
            className={`font-bold text-white tracking-tight flex items-center gap-2 ${
              isMobile ? "text-lg" : "text-2xl"
            }`}
          >
            <span className="text-orange-500">Qhome</span>{" "}
            {!isMobile && "Virtual Office"}
            {!isMobile && (
              <span className="text-xs font-mono font-normal px-2 py-0.5 bg-slate-800 rounded text-slate-400 border border-slate-700">
                v0.15.0
              </span>
            )}
          </h1>

          {/* Breadcrumb — only when in building/floor view */}
          {!isMobile && <Breadcrumb />}
        </div>

        {/* Centered status toast */}
        <div className="absolute left-1/3 -translate-x-1/2 flex items-center pointer-events-none">
          <StatusToast message={statusMessage} />
        </div>

        {!isMobile && (
          <HeaderControls
            isConnected={isConnected}
            debugMode={debugMode}
            aiSummaryEnabled={aiSummaryEnabled}
            onSimulate={handleSimulate}
            onReset={handleReset}
            onClearDB={() => setIsClearModalOpen(true)}
            onToggleDebug={handleToggleDebug}
            onOpenSettings={() => setIsSettingsModalOpen(true)}
            onOpenHelp={() => setIsHelpModalOpen(true)}
          />
        )}

        {isMobile && (
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                isConnected ? "bg-emerald-400 animate-pulse" : "bg-rose-500"
              }`}
            />
            <span className="text-xs text-slate-400 font-mono">
              {agents.size} {t("header.agents")}
            </span>
          </div>
        )}
      </header>

      {/* ----------------------------------------------------------------
          Mobile Drawer
      ---------------------------------------------------------------- */}
      <MobileDrawer
        isOpen={isMobile && mobileMenuOpen}
        sessions={sessions}
        sessionsLoading={sessionsLoading}
        sessionId={sessionId}
        onClose={() => setMobileMenuOpen(false)}
        onSessionSelect={handleSessionSelect}
        onSimulate={handleSimulate}
        onReset={handleReset}
        onClearDB={() => {
          setIsClearModalOpen(true);
          setMobileMenuOpen(false);
        }}
      />

      {/* ----------------------------------------------------------------
          Main Content
      ---------------------------------------------------------------- */}
      {isMobile ? (
        <div className="flex-grow flex flex-col gap-1.5 overflow-hidden min-h-0">
          <div className="flex-[3] border border-slate-800 rounded-lg shadow-2xl bg-slate-900 overflow-hidden relative min-h-0">
            <OfficeGame />
          </div>
          <MobileAgentActivity agents={agents} boss={boss} />
        </div>
      ) : view === "single" ? (
        /* ----------------------------------------------------------------
            Single View (default, original layout)
        ---------------------------------------------------------------- */
        <div className="flex-grow flex gap-2 overflow-hidden min-h-0">
          <SessionSidebar
            sessions={sessions}
            sessionsLoading={sessionsLoading}
            sessionId={sessionId}
            isCollapsed={leftSidebarCollapsed}
            onToggleCollapsed={() =>
              setLeftSidebarCollapsed(!leftSidebarCollapsed)
            }
            onSessionSelect={handleSessionSelect}
            onDeleteSession={setSessionPendingDelete}
            onRenameSession={handleRenameSession}
          />

          <div
            data-tour-id="game-canvas"
            className="flex-grow border border-slate-800 rounded-lg shadow-2xl bg-slate-900 overflow-hidden relative"
          >
            <OfficeGame />
          </div>

          <RightSidebar />
        </div>
      ) : (
        /* ----------------------------------------------------------------
            Building / Floor View (animated transitions)
        ---------------------------------------------------------------- */
        <ViewTransition
          view={view}
          buildingView={<BuildingView sessions={sessions} />}
          floorView={
            <FloorView
              sessions={sessions}
              sessionsLoading={sessionsLoading}
              sessionId={sessionId}
              isCollapsed={leftSidebarCollapsed}
              onToggleCollapsed={() =>
                setLeftSidebarCollapsed(!leftSidebarCollapsed)
              }
              onSessionSelect={handleSessionSelect}
              onDeleteSession={setSessionPendingDelete}
              onRenameSession={handleRenameSession}
            />
          }
        />
      )}

      {/* ----------------------------------------------------------------
          Attention System
      ---------------------------------------------------------------- */}
      <CommandBar />
      <AttentionToasts />
      <AgentPopup />

      {/* ----------------------------------------------------------------
          HITL Supervisor Decision Portal Modal
      ---------------------------------------------------------------- */}
      {hitlSessionId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-200">
          <div className="bg-slate-900/95 border border-amber-500/30 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
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
                  <p className="text-xs text-slate-400 font-mono">Session ID: {hitlSessionId}</p>
                </div>
              </div>
              <button
                onClick={() => {
                  dismissedSessionsRef.current.add(hitlSessionId);
                  setHitlSessionId(null);
                }}
                className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Content */}
            <div className="px-6 py-6 text-slate-300 text-sm leading-relaxed overflow-y-auto flex-1 min-h-0 space-y-6">
              {hitlLoading ? (
                <div className="space-y-4 py-8">
                  <div className="h-4 bg-slate-800 rounded w-1/3 animate-pulse"></div>
                  <div className="h-24 bg-slate-800 rounded animate-pulse"></div>
                  <div className="h-4 bg-slate-800 rounded w-1/2 animate-pulse"></div>
                  <div className="h-20 bg-slate-800 rounded animate-pulse"></div>
                </div>
              ) : hitlDetail ? (
                <>
                  {/* Alert / Notification Ribbon */}
                  {hitlDetail.status === "pending_hitl" ? (
                    <div className="flex items-start gap-3 p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                      <AlertTriangle className="text-amber-500 shrink-0 mt-0.5" size={18} />
                      <div className="space-y-1">
                        <p className="text-xs font-bold text-amber-400 uppercase tracking-wider font-mono">
                          High Value Compensation Requires Action
                        </p>
                        <p className="text-xs text-slate-300">
                          Autonomous agent pipeline proposed a compensation of{" "}
                          <span className="font-bold text-white">
                            Rp {hitlDetail.compensation_value_idr?.toLocaleString("id-ID") || "0"}
                          </span>{" "}
                          which exceeds the auto-release threshold (Rp 1,000,000). Please review and approve/reject.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className={`flex items-start gap-3 p-4 border rounded-xl ${
                      hitlDetail.status === "approved" 
                        ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" 
                        : "bg-rose-500/10 border-rose-500/20 text-rose-400"
                    }`}>
                      <Check className="shrink-0 mt-0.5" size={18} />
                      <div className="space-y-1">
                        <p className="text-xs font-bold uppercase tracking-wider font-mono">
                          Keputusan Keluhan Telah Diproses
                        </p>
                        <p className="text-xs text-slate-300">
                          Status tindakan ini adalah{" "}
                          <span className="font-bold text-white uppercase">{hitlDetail.status}</span>.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Customer & Order Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-3">
                      <h4 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1.5 font-mono">
                        <User size={14} className="text-indigo-400" /> Customer Info
                      </h4>
                      <div className="space-y-1">
                        <p className="text-sm font-semibold text-white">
                          {hitlDetail.customer_name || "Unknown"}
                        </p>
                        <p className="text-xs text-slate-400 font-mono">ID: {hitlDetail.customer_id || "N/A"}</p>
                        <div className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-xs font-mono">
                          Sentiment:{" "}
                          <span className={hitlDetail.sentiment_score && hitlDetail.sentiment_score < 0.3 ? "text-rose-400 font-bold" : "text-emerald-400"}>
                            {hitlDetail.sentiment_score ? hitlDetail.sentiment_score.toFixed(2) : "N/A"}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-3">
                      <h4 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1.5 font-mono">
                        <ShoppingBag size={14} className="text-sky-400" /> Order Details
                      </h4>
                      <div className="space-y-1">
                        <p className="text-sm font-semibold text-white">
                          Order ID: <span className="font-mono text-purple-400">{hitlDetail.order_id || "N/A"}</span>
                        </p>
                        <p className="text-xs text-slate-400">Complaint Type: {hitlDetail.complaint_type || "N/A"}</p>
                        <div className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-xs font-mono">
                          Stock:{" "}
                          <span className={hitlDetail.stock_status === "Available" ? "text-emerald-400" : "text-rose-400 font-semibold"}>
                            {hitlDetail.stock_status || "N/A"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Raw Complaint Message */}
                  <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-2">
                    <h4 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1.5 font-mono">
                      <FileText size={14} className="text-amber-400" /> Pesan Keluhan Pelanggan
                    </h4>
                    <p className="text-xs italic text-slate-300 font-sans border-l-2 border-slate-700 pl-3 leading-relaxed">
                      "{hitlDetail.raw_input}"
                    </p>
                  </div>

                  {/* Claims Audit & Suggested Action */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-3">
                      <h4 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1.5 font-mono">
                        <CheckCircle2 size={14} className="text-emerald-400" /> Claims Audit
                      </h4>
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                          <span className="text-slate-400">Claim Validity</span>
                          <span className={`font-bold ${hitlDetail.claim_valid ? "text-emerald-400" : "text-rose-400"}`}>
                            {hitlDetail.claim_valid ? "VALID ✅" : "INVALID ❌"}
                          </span>
                        </div>
                        <div className="space-y-1">
                          <span className="text-slate-400">Audit Notes:</span>
                          <p className="text-[11px] text-slate-300 bg-slate-900 p-2 rounded border border-slate-800 font-mono">
                            {hitlDetail.audit_notes || "No notes from Logistics Auditor."}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-3">
                      <h4 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1.5 font-mono">
                        <ShieldAlert size={14} className="text-orange-400" /> AI Recommendation Analysis
                      </h4>
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                          <span className="text-slate-400">Decision Type</span>
                          <span className="font-bold text-white uppercase px-2 py-0.5 bg-amber-500/20 border border-amber-500/30 rounded">
                            {hitlDetail.decision_type || "N/A"}
                          </span>
                        </div>
                        <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                          <span className="text-slate-400">Compensation Value</span>
                          <span className="font-bold text-emerald-400 text-sm">
                            Rp {hitlDetail.compensation_value_idr?.toLocaleString("id-ID") || "0"}
                          </span>
                        </div>
                        <div className="flex justify-between items-center py-1">
                          <span className="text-slate-400">Requires ACC</span>
                          <span className="text-amber-400 font-bold font-mono">YES (&gt; Rp 1M)</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Reasoning Chain */}
                  <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-2">
                    <h4 className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1.5 font-mono">
                      🧠 AI Justification Reasoning (Chain of Thought)
                    </h4>
                    <p className="text-[11px] text-slate-300 font-mono bg-slate-950 p-3 rounded-lg border border-slate-800 max-h-32 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                      {hitlDetail.chain_of_thought || "No reasoning chain provided."}
                    </p>
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center text-center p-6 border border-slate-800 bg-slate-900/20 rounded-xl gap-2">
                  <AlertTriangle size={36} className="text-slate-500" />
                  <h3 className="font-bold text-white">Detail tidak ditemukan</h3>
                  <p className="text-xs text-slate-400">Gagal mengambil data untuk ID tersebut.</p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-900/50 flex-shrink-0">
              <div className="text-xs text-slate-400">
                Status: <span className="font-bold text-amber-500 font-mono uppercase">{hitlDetail?.status || "Unknown"}</span>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleHitlAction("reject")}
                  disabled={hitlActionLoading || hitlLoading || hitlDetail?.status !== "pending_hitl"}
                  className="inline-flex items-center gap-2 px-4 py-2 border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 disabled:opacity-30 disabled:hover:bg-rose-500/10 text-rose-400 hover:text-rose-300 text-sm font-bold rounded-xl transition-all"
                >
                  Tolak Pengajuan
                </button>
                <button
                  onClick={() => handleHitlAction("approve")}
                  disabled={hitlActionLoading || hitlLoading || hitlDetail?.status !== "pending_hitl"}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-30 disabled:from-emerald-600/50 disabled:to-teal-600/50 text-white text-sm font-bold rounded-xl transition-all shadow-lg shadow-emerald-950/30 hover:scale-[1.02] active:scale-[0.98]"
                >
                  <Check size={16} />
                  Setujui & Proses
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ----------------------------------------------------------------
          Tour Overlay
      ---------------------------------------------------------------- */}
      <TourOverlay />
    </main>
  );
}
