"use client";

import { create } from "zustand";
import type {
  ViewMode,
  BuildingConfig,
  FloorConfig,
  TransitionDirection,
} from "@/types/navigation";

// ============================================================================
// TYPES
// ============================================================================

interface NavigationState {
  view: ViewMode;
  floorId: string | null;
  buildingConfig: BuildingConfig | null;
  isLoading: boolean;
  transitionOrigin: { x: number; y: number } | null;
  transitionDirection: TransitionDirection;
  isTransitioning: boolean;
  pendingEditBuilding: boolean;
  /** Map of floorId → unlocked (persisted in sessionStorage per floor) */
  unlockedFloors: Record<string, boolean>;
}

interface NavigationActions {
  goToBuilding: () => void;
  goToFloor: (floorId: string) => void;
  setBuildingConfig: (config: BuildingConfig) => void;
  updateBuildingConfig: (config: BuildingConfig) => void;
  setLoading: (loading: boolean) => void;
  setTransitionOrigin: (origin: { x: number; y: number } | null) => void;
  completeTransition: () => void;
  getCurrentFloor: () => FloorConfig | null;
  resetToSingle: () => void;
  requestEditBuilding: () => void;
  consumeEditBuilding: () => boolean;
  /** Unlock a floor by floorId */
  unlockFloor: (floorId: string) => void;
  /** Lock a floor by floorId */
  lockFloor: (floorId: string) => void;
  /** Check if a floor is unlocked */
  isFloorUnlocked: (floorId: string) => boolean;
  // Legacy aliases for archive floor (backward compat)
  unlockArchive: () => void;
  lockArchive: () => void;
  archiveUnlocked: boolean;
}

type NavigationStore = NavigationState & NavigationActions;

// ============================================================================
// HELPERS
// ============================================================================

function sessionKey(floorId: string): string {
  return `unlocked_floor_${floorId}`;
}

function loadUnlockedFloors(): Record<string, boolean> {
  if (typeof window === "undefined") return {};
  const result: Record<string, boolean> = {};
  for (let i = 0; i < sessionStorage.length; i++) {
    const k = sessionStorage.key(i);
    if (k?.startsWith("unlocked_floor_") && sessionStorage.getItem(k) === "1") {
      result[k.replace("unlocked_floor_", "")] = true;
    }
  }
  return result;
}

// ============================================================================
// STORE
// ============================================================================

export const useNavigationStore = create<NavigationStore>()((set, get) => ({
  view: "single",
  floorId: null,
  buildingConfig: null,
  isLoading: false,
  transitionOrigin: null,
  transitionDirection: null,
  isTransitioning: false,
  pendingEditBuilding: false,
  unlockedFloors: loadUnlockedFloors(),

  // ── Legacy computed getter for archive backward compat ───────────────────
  get archiveUnlocked() {
    return get().unlockedFloors["archive"] === true;
  },

  goToBuilding: () =>
    set({
      view: "building",
      floorId: null,
      transitionDirection: "zoom-out",
      isTransitioning: true,
    }),

  goToFloor: (floorId) =>
    set({
      view: "floor",
      floorId,
      transitionDirection: "zoom-in",
      isTransitioning: true,
    }),

  setBuildingConfig: (config) =>
    set((state) => {
      const hasFloors = config.floors.length > 0;
      const currentView = state.view;
      const newView: ViewMode =
        currentView === "single" && hasFloors
          ? "building"
          : currentView === "single"
            ? "single"
            : currentView;
      return { buildingConfig: config, isLoading: false, view: newView };
    }),

  updateBuildingConfig: (config) => set({ buildingConfig: config }),

  setLoading: (loading) => set({ isLoading: loading }),

  setTransitionOrigin: (origin) => set({ transitionOrigin: origin }),

  completeTransition: () =>
    set({
      isTransitioning: false,
      transitionDirection: null,
      transitionOrigin: null,
    }),

  getCurrentFloor: () => {
    const { buildingConfig, floorId } = get();
    if (!buildingConfig || !floorId) return null;
    return buildingConfig.floors.find((f) => f.id === floorId) ?? null;
  },

  resetToSingle: () =>
    set({
      view: "single",
      floorId: null,
      buildingConfig: null,
      transitionDirection: null,
      isTransitioning: false,
      transitionOrigin: null,
    }),

  requestEditBuilding: () => set({ pendingEditBuilding: true }),

  consumeEditBuilding: () => {
    const pending = get().pendingEditBuilding;
    if (pending) set({ pendingEditBuilding: false });
    return pending;
  },

  unlockFloor: (floorId) => {
    sessionStorage.setItem(sessionKey(floorId), "1");
    set((s) => ({ unlockedFloors: { ...s.unlockedFloors, [floorId]: true } }));
  },

  lockFloor: (floorId) => {
    sessionStorage.removeItem(sessionKey(floorId));
    set((s) => {
      const next = { ...s.unlockedFloors };
      delete next[floorId];
      return { unlockedFloors: next };
    });
  },

  isFloorUnlocked: (floorId) => get().unlockedFloors[floorId] === true,

  // Legacy aliases
  unlockArchive: () => get().unlockFloor("archive"),
  lockArchive: () => get().lockFloor("archive"),
}));
