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
  error?: string;
}

export interface VisualPayload {
  insight: string;
  tip: string;
}

export interface FeedbackPayload {
  feedback_type: string;
  relevance_score: number;
  key_concern: string;
  critical_question: string;
  cultural_note: string | null;
  recommendation: string;
  alignment_with_values: string;
  setting: string;
  group: string;
  location: string;
  culture: string;
}

export interface GraphGroup {
  group: string;
  engagement: number;
  impact: number;
}

export type InsightCategory = "grammar" | "engagement" | "clarity" | "structure" | "delivery";

export interface LiveAIInsight {
  category: InsightCategory;
  text: string;
}

export interface DocumentAnalysisPayload {
  doc_type: "presentation" | "report" | "other";
  paragraphs: string[];
  success_scores: { audience: number; environment: number; complexity: number };
  language_tone: "professional" | "casual";
  short_feedback: string;
  live_ai_items: LiveAIInsight[];
  graph_data: {
    by_age: GraphGroup[];
    by_type: GraphGroup[];
  };
}

export interface FileQueueItem {
  uid: number;
  name: string;
  file: File;
}

export type AgentEventType = "speech" | "audience" | "cultural" | "coaching" | "visual" | "feedback";

export interface AgentEvent {
  id: number;
  agent: AgentEventType;
  payload: SpeechPayload | AudiencePayload | CulturalPayload | CoachingPayload | VisualPayload | FeedbackPayload;
  timestamp: number;
}

export interface SessionConfig {
  personaType: string;
  region: string;
  focusArea: string;
  environment: string;
  complexity: string;
  feedbackSetting?: string;
  audienceMinAge?: number;
  audienceMaxAge?: number;
  audienceAmount?: number;
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
  latestVisual: VisualPayload | null;
  feedbacks: FeedbackPayload[];
  latestDocumentAnalysis: DocumentAnalysisPayload | null;
  latestFilename: string | null;
  liveAIInsights: LiveAIInsight[];
  fileQueue: FileQueueItem[];

  setSessionId: (id: string) => void;
  setSessionConfig: (config: Partial<SessionConfig>) => void;
  setConnected: (connected: boolean) => void;
  addEvent: (agent: AgentEventType, payload: AgentEvent["payload"]) => void;
  setDocumentAnalysis: (payload: DocumentAnalysisPayload | null) => void;
  setFilename: (name: string | null) => void;
  setLiveAIInsights: (items: LiveAIInsight[]) => void;
  enqueueFile: (file: File) => void;
  dequeueFile: (uid: number) => void;
  clearFileQueue: () => void;
  clearSession: () => void;
}

let _counter = 0;
let _fileCounter = 0;

export const useStore = create<Store>((set) => ({
  sessionId: null,
  sessionConfig: {
    personaType: "executive",
    region: "us",
    focusArea: "business",
    environment: "professional",
    complexity: "medium",
    feedbackSetting: "academic_us",
    audienceMinAge: 18,
    audienceMaxAge: 45,
    audienceAmount: 100,
  },
  isConnected: false,
  events: [],
  latestSpeech: null,
  latestAudience: null,
  latestCultural: null,
  latestCoaching: null,
  latestVisual: null,
  feedbacks: [],
  latestDocumentAnalysis: null,
  latestFilename: null,
  liveAIInsights: [],
  fileQueue: [],

  setSessionId: (id) => set({ sessionId: id }),
  setSessionConfig: (config) =>
    set((s) => ({ sessionConfig: { ...s.sessionConfig, ...config } })),
  setConnected: (connected) => set({ isConnected: connected }),

  addEvent: (agent, payload) => {
    const event: AgentEvent = { id: ++_counter, agent, payload, timestamp: Date.now() };
    set((s) => ({
      events: [...s.events.slice(-49), event],
      ...(agent === "speech"   && { latestSpeech:   payload as SpeechPayload }),
      ...(agent === "audience" && { latestAudience: payload as AudiencePayload }),
      ...(agent === "cultural" && { latestCultural: payload as CulturalPayload }),
      ...(agent === "coaching" && { latestCoaching: payload as CoachingPayload }),
      ...(agent === "visual"   && { latestVisual:   payload as VisualPayload }),
      ...(agent === "feedback" && { feedbacks: [...s.feedbacks.slice(-9), payload as FeedbackPayload] }),
    }));
  },

  setDocumentAnalysis: (payload) => set({ latestDocumentAnalysis: payload }),
  setFilename: (name) => set({ latestFilename: name }),
  setLiveAIInsights: (items) => set({ liveAIInsights: items }),

  enqueueFile: (file) =>
    set((s) => {
      if (s.fileQueue.length >= 3) return s;
      return { fileQueue: [...s.fileQueue, { uid: ++_fileCounter, name: file.name, file }] };
    }),

  dequeueFile: (uid) =>
    set((s) => ({ fileQueue: s.fileQueue.filter((f) => f.uid !== uid) })),

  clearFileQueue: () => set({ fileQueue: [] }),

  clearSession: () =>
    set({
      sessionId: null,
      isConnected: false,
      events: [],
      latestSpeech: null,
      latestAudience: null,
      latestCultural: null,
      latestCoaching: null,
      latestVisual: null,
      feedbacks: [],
      latestDocumentAnalysis: null,
      liveAIInsights: [],
      // latestFilename, fileQueue intentionally kept — Documents panel + LiveAI never auto-clear
    }),
}));
