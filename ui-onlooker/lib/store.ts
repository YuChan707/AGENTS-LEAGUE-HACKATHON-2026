import { create } from "zustand";

export interface SpeechPayload {
  pace_wpm: number;
  filler_count: number;
  filler_words: string[];
  word_count: number;
  clarity_score: number;
}

export interface AudiencePayload {
  speaker: string;
  role: string;
  reaction_type: string;
  body_language: string;
  internal_thought: string;
  would_ask: string;
}

export interface CulturalPayload {
  flag: boolean;
  issue: string;
  fix: string;
}

export interface CoachingPayload {
  tip: string;
}

export type AgentEventType = "speech" | "audience" | "cultural" | "coaching";

export interface AgentEvent {
  id: number;
  agent: AgentEventType;
  payload: SpeechPayload | AudiencePayload | CulturalPayload | CoachingPayload;
  timestamp: number;
}

export interface SessionConfig {
  personaType: string;
  region: string;
  focusArea: string;
}

interface Store {
  sessionId: string | null;
  sessionConfig: SessionConfig;
  isConnected: boolean;
  events: AgentEvent[];
  latestSpeech: SpeechPayload | null;
  latestAudience: AudiencePayload | null;
  latestCultural: CulturalPayload | null;
  latestCoaching: CoachingPayload | null;

  setSessionId: (id: string) => void;
  setSessionConfig: (config: Partial<SessionConfig>) => void;
  setConnected: (connected: boolean) => void;
  addEvent: (agent: AgentEventType, payload: AgentEvent["payload"]) => void;
  clearSession: () => void;
}

let _counter = 0;

export const useStore = create<Store>((set) => ({
  sessionId: null,
  sessionConfig: { personaType: "executive", region: "us", focusArea: "business" },
  isConnected: false,
  events: [],
  latestSpeech: null,
  latestAudience: null,
  latestCultural: null,
  latestCoaching: null,

  setSessionId: (id) => set({ sessionId: id }),
  setSessionConfig: (config) =>
    set((s) => ({ sessionConfig: { ...s.sessionConfig, ...config } })),
  setConnected: (connected) => set({ isConnected: connected }),

  addEvent: (agent, payload) => {
    const event: AgentEvent = { id: ++_counter, agent, payload, timestamp: Date.now() };
    set((s) => ({
      events: [...s.events.slice(-49), event],
      ...(agent === "speech" && { latestSpeech: payload as SpeechPayload }),
      ...(agent === "audience" && { latestAudience: payload as AudiencePayload }),
      ...(agent === "cultural" && { latestCultural: payload as CulturalPayload }),
      ...(agent === "coaching" && { latestCoaching: payload as CoachingPayload }),
    }));
  },

  clearSession: () =>
    set({
      sessionId: null,
      isConnected: false,
      events: [],
      latestSpeech: null,
      latestAudience: null,
      latestCultural: null,
      latestCoaching: null,
    }),
}));
