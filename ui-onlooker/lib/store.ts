// Zustand global state for the dashboard.
// Scaffold: holds session config, agent statuses, scores, and live feeds.
// Fill in the slices as the UI is built.

import { create } from "zustand";

export interface AppState {
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
}

export const useStore = create<AppState>((set) => ({
  sessionId: null,
  setSessionId: (id) => set({ sessionId: id }),
}));
