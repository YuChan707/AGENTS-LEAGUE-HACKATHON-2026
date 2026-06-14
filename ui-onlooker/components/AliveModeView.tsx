"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Monitor, RotateCcw, Pause, Play, CirclePlay as PlayCircle, Bot, Send,
} from "lucide-react";
import { Airplay } from "@deemlol/next-icons";
import {
  useStore,
  AgentEvent,
  AudiencePayload,
  CoachingPayload,
  DocumentAnalysisPayload,
  SpeechPayload,
  VisualPayload,
} from "@/lib/store";
import { useWebSocket } from "@/lib/useWebSocket";
import AnalysisGraphPanel from "@/components/AnalysisGraphPanel";

const API_BASE =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) ||
  "http://localhost:8000";

// ── helpers ──────────────────────────────────────────────────────────────────

const FALLBACK_FEED = [
  { color: "var(--color-btn-action)", text: "Audience engagement is peaking. Keep this pace." },
  { color: "var(--color-on-surface)", text: "Someone mentioned the data source is unclear." },
  { color: "var(--color-secondary)", text: "Attention dropping in the front rows. Use a gesture." },
  { color: "var(--color-btn-action)", text: "Great point about the methodology!" },
];

function toFeedItem(e: AgentEvent): { color: string; text: string } {
  if (e.agent === "coaching") {
    return { color: "var(--color-btn-action)", text: (e.payload as CoachingPayload).tip };
  }
  if (e.agent === "visual") {
    return { color: "var(--color-secondary)", text: `\u{1F441} ${(e.payload as VisualPayload).tip}` };
  }
  const p = e.payload as AudiencePayload;
  return { color: "var(--color-on-surface)", text: `${p.speaker}: "${p.internal_thought}"` };
}

const MOOD_MAP: [string, string][] = [
  ["excit",    "excite"],
  ["enthus",   "excite"],
  ["impress",  "great"],
  ["great",    "great"],
  ["positive", "clear"],
  ["engag",    "clear"],
  ["curious",  "clear"],
  ["clear",    "clear"],
  ["neutral",  "clear"],
  ["confus",   "confuse"],
  ["disengage","confuse"],
  ["unclear",  "confuse"],
  ["bored",    "terrible"],
  ["hostile",  "terrible"],
  ["negative", "terrible"],
];

function deriveMood(reaction: string): string {
  const lower = reaction.toLowerCase();
  for (const [key, word] of MOOD_MAP) {
    if (lower.includes(key)) return word;
  }
  return "clear";
}

function fmtAmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1).replace(".0", "")}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1).replace(".0", "")}k`;
  return n.toLocaleString();
}

function complexityColor(v: string) {
  if (v === "easy")    return "#107c10";
  if (v === "medium")  return "#f59e0b";
  if (v === "complex") return "#c4362c";
  return "var(--color-on-surface)";
}

function moodColor(v: string) {
  if (v === "terrible") return "#c4362c";
  if (v === "confuse")  return "#f59e0b";
  if (v === "excite" || v === "great") return "#107c10";
  if (v === "clear")   return "var(--color-btn-action)";
  return "var(--color-on-surface)";
}

interface PostMetrics {
  complexity: string;
  attention:  string;
  mood:       string;
  questions:  string[];
}

// ── main component ────────────────────────────────────────────────────────────

interface AliveModeViewProps {
  onShareError?: () => void;
  onShareStatusChange?: (status: "idle" | "active" | "denied" | "paused") => void;
  metrics?: Partial<{ attention: string; mood: string; liveAudience: string; questions: string; complexity: string }>;
}

export default function AliveModeView({ onShareError, onShareStatusChange }: AliveModeViewProps) {
  const [shareStatus, setShareStatus]               = useState<"idle" | "active" | "denied">("idle");
  const [recordPaused, setRecordPaused]             = useState(false);
  const [elapsed, setElapsed]                       = useState(0);
  const [instruction, setInstruction]               = useState("");
  const [instructionSending, setInstructionSending] = useState(false);
  const [postMetrics, setPostMetrics]               = useState<PostMetrics | null>(null);
  const [aliveDocAnalysis, setAliveDocAnalysis]     = useState<DocumentAnalysisPayload | null>(null);
  const [showFeedbackModal, setShowFeedbackModal]   = useState(false);
  const [hasSharedBefore, setHasSharedBefore]       = useState(false);

  const events        = useStore((s) => s.events);
  const sessionId     = useStore((s) => s.sessionId);
  const sessionConfig = useStore((s) => s.sessionConfig);
  const addEvent      = useStore((s) => s.addEvent);

  const settingsReady = !!sessionId;
  const wsRef = useRef(useWebSocket());

  const streamRef     = useRef<MediaStream | null>(null);
  const videoRef      = useRef<HTMLVideoElement>(null);
  const recordPausedRef = useRef(false);
  // sessionStartRef is used in callbacks; sessionStartState drives the render-time useMemo
  const sessionStartRef = useRef(0);
  const [sessionStartState, setSessionStartState] = useState(0);
  const eventsRef     = useRef(events);
  const transcriptRef = useRef("");
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => { recordPausedRef.current = recordPaused; }, [recordPaused]);
  useEffect(() => { eventsRef.current = events; }, [events]);

  // Events that belong to this alive session only (uses state, not ref, to avoid render-time ref access)
  const sessionEvents = useMemo(() => events.slice(sessionStartState), [events, sessionStartState]);

  // Rolling AI feed
  const liveFeed = sessionEvents
    .filter((e) => e.agent === "coaching" || e.agent === "audience" || e.agent === "visual")
    .slice(-4)
    .map(toFeedItem);
  const feed = liveFeed.length > 0 ? liveFeed : FALLBACK_FEED;

  // Real-time overlay values (during session)
  const rtSpeech   = [...sessionEvents].reverse().find((e) => e.agent === "speech")?.payload as SpeechPayload | undefined;
  const rtAudience = [...sessionEvents].reverse().find((e) => e.agent === "audience")?.payload as AudiencePayload | undefined;
  const rtAttention = rtSpeech ? `${Math.round(rtSpeech.clarity_score * 100)}%` : "--";
  const rtMood      = rtAudience ? deriveMood(rtAudience.reaction_type) : "--";

  // Audience count from settings (live)
  const audienceDisplay = sessionConfig.audienceAmount ? fmtAmt(sessionConfig.audienceAmount) : "--";

  // Compute post-session metrics from captured events
  function computePostMetrics(): PostMetrics {
    const evts      = eventsRef.current.slice(sessionStartRef.current);
    const speechEvts = evts.filter((e) => e.agent === "speech").map((e) => e.payload as SpeechPayload);
    const audEvts    = evts.filter((e) => e.agent === "audience").map((e) => e.payload as AudiencePayload);

    const avgPace = speechEvts.length
      ? speechEvts.reduce((s, e) => s + e.pace_wpm, 0) / speechEvts.length
      : null;
    const complexity = avgPace === null ? "--"
      : avgPace > 160 ? "complex"
      : avgPace > 110 ? "medium"
      : "easy";

    const avgClarity = speechEvts.length
      ? speechEvts.reduce((s, e) => s + e.clarity_score, 0) / speechEvts.length
      : null;
    const attention = avgClarity !== null ? `${Math.round(avgClarity * 100)}%` : "--";

    const reactions = audEvts.map((e) => e.reaction_type).filter(Boolean);
    const mood = reactions.length ? deriveMood(reactions[reactions.length - 1]) : "--";

    const questions = [...new Set(audEvts.map((e) => e.would_ask).filter(Boolean))].slice(0, 6);

    return { complexity, attention, mood, questions };
  }

  // Build AnalysisGraphPanel-compatible data from session events
  function buildGraph(): DocumentAnalysisPayload {
    const evts       = eventsRef.current.slice(sessionStartRef.current);
    const speechEvts = evts.filter((e) => e.agent === "speech").map((e) => e.payload as SpeechPayload);
    const avgClarity = speechEvts.length
      ? speechEvts.reduce((s, e) => s + e.clarity_score, 0) / speechEvts.length
      : 0.6;
    const eng    = Math.round(avgClarity * 100);
    const minAge = sessionConfig.audienceMinAge ?? 18;
    const maxAge = sessionConfig.audienceMaxAge ?? 45;
    const mid    = Math.round((minAge + maxAge) / 2);
    const persona = sessionConfig.personaType
      ? sessionConfig.personaType.charAt(0).toUpperCase() + sessionConfig.personaType.slice(1)
      : "General";
    return {
      doc_type: "other",
      paragraphs: [],
      success_scores: {
        audience:    eng,
        environment: Math.min(eng + 5, 100),
        complexity:  Math.max(eng - 5, 0),
      },
      language_tone: "professional",
      short_feedback: transcriptRef.current
        ? "Analysis derived from live voice and screen content."
        : "Analysis derived from live screen content.",
      live_ai_items: [],
      graph_data: {
        by_age: [
          { group: `${minAge}–${mid}`, engagement: Math.max(20, eng - 8),  impact: Math.max(15, eng - 12) },
          { group: `${mid}–${maxAge}`, engagement: Math.min(100, eng + 5), impact: Math.min(100, eng + 2) },
        ],
        by_type: [
          { group: persona,   engagement: eng,                         impact: Math.max(20, eng - 5)  },
          { group: "General", engagement: Math.max(20, eng - 12),     impact: Math.max(15, eng - 15) },
        ],
      },
    };
  }

  // ── timers & capture ─────────────────────────────────────────────────────

  useEffect(() => {
    if (shareStatus !== "active") return;
    const id = setInterval(() => {
      if (!recordPausedRef.current) setElapsed((s) => s + 1);
    }, 1000);
    return () => { clearInterval(id); setElapsed(0); };
  }, [shareStatus]);

  useEffect(() => {
    if (shareStatus !== "active") return;
    const canvas = document.createElement("canvas");
    const ctx2d  = canvas.getContext("2d");
    const capture = () => {
      const video = videoRef.current;
      if (!video || video.readyState < 2 || !ctx2d) return;
      canvas.width  = Math.min(video.videoWidth, 1280);
      canvas.height = Math.round(canvas.width * (video.videoHeight / Math.max(video.videoWidth, 1)));
      ctx2d.drawImage(video, 0, 0, canvas.width, canvas.height);
      const b64 = canvas.toDataURL("image/jpeg", 0.6).split(",")[1];
      if (b64) wsRef.current.sendFrame(b64);
    };
    const id = setInterval(capture, 8000);
    return () => clearInterval(id);
  }, [shareStatus]);

  // Voice recognition (Web Speech API)
  useEffect(() => {
    if (shareStatus !== "active") {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch { /* ignore */ }
        recognitionRef.current = null;
      }
      return;
    }
    const SpeechRecAPI: typeof SpeechRecognition | undefined =
      window.SpeechRecognition ??
      (window as Window & { webkitSpeechRecognition?: typeof SpeechRecognition }).webkitSpeechRecognition;
    if (!SpeechRecAPI) return;

    const rec = new SpeechRecAPI();
    rec.continuous     = true;
    rec.interimResults = false;
    rec.lang           = "en-US";
    rec.onresult = (ev: SpeechRecognitionEvent) => {
      const text = Array.from(ev.results).map((r) => r[0].transcript).join(" ");
      transcriptRef.current = text;
      wsRef.current.sendTranscript(text);
    };
    rec.onerror = () => { /* silently ignore mic errors */ };
    try { rec.start(); } catch { /* ignore */ }
    recognitionRef.current = rec;
    return () => { try { rec.stop(); } catch { /* ignore */ } recognitionRef.current = null; };
  }, [shareStatus]);

  // ── stream controls ───────────────────────────────────────────────────────

  const requestShare = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;

      sessionStartRef.current = eventsRef.current.length;
      setSessionStartState(eventsRef.current.length);
      transcriptRef.current   = "";
      setShareStatus("active");
      setPostMetrics(null);
      setAliveDocAnalysis(null);
      onShareStatusChange?.("active");
      wsRef.current.connect();

      stream.getTracks()[0].addEventListener("ended", () => {
        setShareStatus("idle");
        setHasSharedBefore(true);
        setPostMetrics(computePostMetrics());
        setAliveDocAnalysis(buildGraph());
        setShowFeedbackModal(true);
        onShareStatusChange?.("idle");
        streamRef.current = null;
        if (videoRef.current) videoRef.current.srcObject = null;
        wsRef.current.disconnect();
      });
    } catch {
      setShareStatus("denied");
      onShareStatusChange?.("denied");
      onShareError?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onShareError, onShareStatusChange]);

  // Cleanup on unmount only
  useEffect(() => {
    return () => { streamRef.current?.getTracks().forEach((t) => t.stop()); };
  }, []);

  const retryShare = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setShareStatus("idle");
    setRecordPaused(false);
    setPostMetrics(null);
    setAliveDocAnalysis(null);
    onShareStatusChange?.("idle");
    requestShare();
  }, [requestShare, onShareStatusChange]);

  const pauseStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => { t.enabled = false; });
    setRecordPaused(true);
    onShareStatusChange?.("paused");
  }, [onShareStatusChange]);

  const resumeStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => { t.enabled = true; });
    setRecordPaused(false);
    onShareStatusChange?.("active");
  }, [onShareStatusChange]);

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setShareStatus("idle");
    setRecordPaused(false);
    setHasSharedBefore(true);
    setPostMetrics(computePostMetrics());
    setAliveDocAnalysis(buildGraph());
    setShowFeedbackModal(true);
    onShareStatusChange?.("idle");
    wsRef.current.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onShareStatusChange]);

  // ── instruction send ──────────────────────────────────────────────────────

  const sendInstruction = async () => {
    const text = instruction.trim();
    if (!text || instructionSending) return;
    setInstructionSending(true);
    try {
      const body = transcriptRef.current
        ? `[Voice transcript]\n${transcriptRef.current}\n\n[Instruction]\n${text}`
        : text;
      const res = await fetch(`${API_BASE}/analyze/chunk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: body,
          session_id: sessionId ?? "alive",
          persona_type: sessionConfig.personaType,
          region: sessionConfig.region,
          focus_area: sessionConfig.focusArea,
          environment: sessionConfig.environment,
          complexity: sessionConfig.complexity,
          feedback_setting: sessionConfig.feedbackSetting ?? "academic_us",
          audience_min_age: sessionConfig.audienceMinAge ?? 18,
          audience_max_age: sessionConfig.audienceMaxAge ?? 45,
          audience_amount: sessionConfig.audienceAmount ?? 100,
        }),
      });
      if (res.ok) {
        const data = await res.json() as { events: AgentEvent[] };
        for (const ev of data.events) addEvent(ev.agent, ev.payload);
      }
    } catch { /* offline / backend down — silently ignore */ } finally {
      setInstructionSending(false);
      setInstruction("");
    }
  };

  const handleInstructionKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendInstruction(); }
  };

  // ── REC time ──────────────────────────────────────────────────────────────

  const recTime = `${String(Math.floor(elapsed / 3600)).padStart(2, "0")}:${String(Math.floor((elapsed % 3600) / 60)).padStart(2, "0")}:${String(elapsed % 60).padStart(2, "0")}`;

  // ── displayed values ──────────────────────────────────────────────────────

  const dispComplexity = postMetrics?.complexity ?? "--";
  const dispAttention  = postMetrics?.attention  ?? "--";
  const dispMood       = postMetrics?.mood       ?? "--";
  const dispQuestions  = postMetrics?.questions  ?? [];
  const cxColor = complexityColor(dispComplexity);
  const mdColor = moodColor(dispMood);

  // Auto-dismiss feedback modal after 5 s
  useEffect(() => {
    if (!showFeedbackModal) return;
    const t = setTimeout(() => setShowFeedbackModal(false), 5000);
    return () => clearTimeout(t);
  }, [showFeedbackModal]);

  // ── render ────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col gap-[var(--sp-lg)] flex-1 relative">

      {/* ── "Look the feedback" modal ── */}
      {showFeedbackModal && (
        <div
          className="absolute inset-x-0 top-0 z-50 flex justify-center pointer-events-none"
          style={{ paddingTop: "var(--sp-md)" }}
        >
          <div
            className="pointer-events-auto flex items-center gap-[var(--sp-md)] px-[var(--sp-lg)] py-[var(--sp-md)] rounded-xl shadow-2xl border"
            style={{
              background: "linear-gradient(135deg, #0078d4 0%, #005fa3 100%)",
              borderColor: "rgba(255,255,255,0.15)",
              color: "#fff",
              maxWidth: 440,
              animation: "slideDown 0.35s cubic-bezier(0.34,1.56,0.64,1)",
            }}
          >
            <span className="material-symbols-outlined flex-shrink-0" style={{ fontSize: 28 }}>analytics</span>
            <div className="flex flex-col gap-[2px]">
              <span style={{ fontSize: "var(--text-body)", fontWeight: 800, letterSpacing: "0.01em" }}>
                Session complete — look the feedback!
              </span>
              <span style={{ fontSize: "var(--text-xs)", opacity: 0.85 }}>
                Complexity · Attention · Mood · Questions · Graph are ready below.
              </span>
            </div>
            <button
              onClick={() => setShowFeedbackModal(false)}
              className="ml-auto flex-shrink-0 rounded p-[var(--sp-xs)] transition-colors"
              style={{ background: "rgba(255,255,255,0.15)", color: "#fff" }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.25)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.15)")}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>close</span>
            </button>
          </div>
        </div>
      )}

      {/* ── Main screen share ── */}
      <section
        className="bg-white border rounded-xl flex flex-col relative overflow-hidden shadow-lg"
        style={{ aspectRatio: "16/9", borderColor: "var(--color-surface-highest)" }}
      >
        {/* bg dot grid */}
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.03]"
          style={{ backgroundImage: "radial-gradient(#000 1px, transparent 1px)", backgroundSize: "20px 20px" }}
        />

        {/* Workspace header */}
        <div
          className="px-[var(--sp-md)] py-[var(--sp-sm)] border-b flex justify-between items-center z-10 bg-white"
          style={{ borderColor: "var(--color-surface-highest)" }}
        >
          <div className="flex items-center gap-[var(--sp-sm)]">
            <Monitor size={22} color="#0078d4" strokeWidth={2} />
            <span style={{ fontSize: "var(--text-xs)", fontWeight: 700, color: "var(--color-on-surface-variant)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Live Stream: "--"
            </span>
          </div>
          <div className="flex items-center gap-[var(--sp-sm)]">
            <div
              className="flex items-center gap-[var(--sp-xs)] px-[var(--sp-sm)] py-[var(--sp-xs)] rounded"
              style={{
                background: shareStatus === "active" ? "rgba(16,124,16,0.1)" : "rgba(186,26,26,0.08)",
                color: shareStatus === "active" ? "#107c10" : "var(--color-error)",
              }}
            >
              <div
                className={`w-2 h-2 rounded-full ${shareStatus === "active" ? "animate-pulse" : ""}`}
                style={{ background: shareStatus === "active" ? "#107c10" : "var(--color-error)" }}
              />
              <span style={{ fontSize: 10, fontWeight: 700 }}>
                {shareStatus === "active" ? "LIVE" : "OFFLINE"}
              </span>
            </div>
            {(shareStatus === "active" || recordPaused) && (
              <span
                className="border rounded px-[var(--sp-xs)]"
                style={{ fontSize: 10, fontWeight: 600, color: "var(--color-on-surface-variant)", borderColor: "var(--color-outline-variant)" }}
              >
                REC {recTime}
              </span>
            )}
            <span
              className="material-symbols-outlined cursor-pointer transition-colors"
              style={{ color: "var(--color-on-surface-variant)", fontSize: 20 }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--color-btn-action)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--color-on-surface-variant)")}
            >
              settings
            </span>
          </div>
        </div>

        {/* Main area */}
        <div className="flex-1 flex relative overflow-hidden" style={{ background: "var(--color-surface-container)" }}>

          {/* Floating AI feedback bar */}
          <div
            className="absolute z-20 pointer-events-none"
            style={{ top: "var(--sp-md)", left: "50%", transform: "translateX(-50%)", width: "75%", maxWidth: 480 }}
          >
            <div
              className="flex items-center gap-[var(--sp-md)] p-[var(--sp-md)] rounded-xl border shadow-2xl"
              style={{ background: "rgba(255,255,255,0.9)", backdropFilter: "blur(12px)", borderColor: "var(--color-surface-highest)" }}
            >
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm"
                style={{ background: "var(--color-btn-action)" }}
              >
                <span className="material-symbols-outlined" style={{ color: "#fff", fontSize: 20 }}>auto_awesome</span>
              </div>
              <div className="overflow-hidden h-6 flex-1">
                <div className="scroll-feed flex flex-col gap-2">
                  {[...feed, ...feed].map((item, i) => (
                    <p key={i} style={{ fontSize: "var(--text-body)", fontWeight: 500, color: item.color, whiteSpace: "nowrap" }}>
                      {item.text}
                    </p>
                  ))}
                </div>
              </div>
              <div className="flex gap-[2px]">
                <div className="w-1 h-1 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
                <div className="w-1 h-1 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
                <div className="w-1 h-1 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
              </div>
            </div>
          </div>

          {/* Window area */}
          <div className="flex-1 relative p-[var(--sp-lg)]">
            <div
              className="w-full h-full rounded-lg shadow-2xl border-[3px] relative overflow-hidden"
              style={{ background: "#ffffff", borderColor: "rgba(0,120,212,0.1)" }}
            >
              {/* Browser chrome bar */}
              <div
                className="absolute top-0 left-0 w-full h-8 flex items-center px-[var(--sp-md)] gap-[var(--sp-xs)] border-b"
                style={{ background: "var(--color-surface-low)", borderColor: "var(--color-surface-highest)", zIndex: 1 }}
              >
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: "#ff5f57" }} />
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: "#febc2e" }} />
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: "#28c840" }} />
                <div className="ml-4" style={{ fontSize: 10, color: "var(--color-on-surface-variant)", fontFamily: "monospace" }}>
                  https://research-slides.app/project-v2
                </div>
              </div>

              {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
              <video
                ref={videoRef}
                autoPlay
                muted
                style={{
                  display: shareStatus === "active" ? "block" : "none",
                  position: "absolute", top: 32, left: 0,
                  width: "100%", height: "calc(100% - 32px)",
                  objectFit: "contain", background: "#000",
                }}
              />

              <div
                className="mt-8 h-full flex flex-col items-center justify-center gap-[var(--sp-md)]"
                style={{ background: "var(--color-surface-container)", display: shareStatus !== "active" ? "flex" : "none" }}
              >
                {shareStatus === "denied" ? (
                  <div className="flex flex-col items-center gap-[var(--sp-sm)]">
                    <div
                      className="flex items-center gap-[var(--sp-sm)] px-[var(--sp-md)] py-[var(--sp-sm)] rounded-lg"
                      style={{ background: "var(--color-error-container)", color: "var(--color-error)" }}
                    >
                      <span className="material-symbols-outlined" style={{ fontSize: 18 }}>warning</span>
                      <span style={{ fontSize: "var(--text-sm)" }}>Screen share was denied. Try again below.</span>
                    </div>
                  </div>
                ) : !settingsReady ? (
                  /* ── Settings gate ── */
                  <div className="flex flex-col items-center gap-[var(--sp-md)] px-[var(--sp-xl)] text-center" style={{ maxWidth: 340 }}>
                    <div
                      className="w-12 h-12 rounded-full flex items-center justify-center"
                      style={{ background: "rgba(245,158,11,0.12)" }}
                    >
                      <span className="material-symbols-outlined" style={{ fontSize: 24, color: "#f59e0b" }}>tune</span>
                    </div>
                    <div className="flex flex-col gap-[var(--sp-xs)]">
                      <span style={{ fontSize: "var(--text-body)", fontWeight: 700, color: "var(--color-on-surface)" }}>
                        Configure your settings first
                      </span>
                      <span style={{ fontSize: "var(--text-sm)", color: "var(--color-on-surface-variant)", lineHeight: "var(--lh-sm)" }}>
                        Fill in your Project Settings on the left panel and click <strong>Update</strong> before starting a live session.
                      </span>
                    </div>
                    <div
                      className="flex items-center gap-[var(--sp-xs)] px-[var(--sp-md)] py-[var(--sp-xs)] rounded-lg border"
                      style={{ borderColor: "#f59e0b", background: "rgba(245,158,11,0.06)", color: "#b45309", fontSize: "var(--text-xs)", fontWeight: 600 }}
                    >
                      <span className="material-symbols-outlined" style={{ fontSize: 14 }}>arrow_back</span>
                      Set Audience · Environment · Complexity → click Update
                    </div>
                  </div>
                ) : (
                  /* ── Normal waiting state ── */
                  <div className="flex flex-col items-center gap-[var(--sp-sm)]" style={{ color: "var(--color-on-surface-variant)" }}>
                    <Monitor size={32} color="#c0c7d4" strokeWidth={1.5} />
                    <span style={{ fontSize: "var(--text-sm)" }}>
                      {postMetrics ? "Session complete — results shown below." : "Waiting for screen share…"}
                    </span>
                    {!postMetrics && (
                      <button
                        onClick={requestShare}
                        className="mt-[var(--sp-sm)] flex items-center gap-[var(--sp-xs)] px-[var(--sp-lg)] py-[var(--sp-sm)] rounded-lg transition-colors"
                        style={{ background: "var(--color-btn-action)", color: "#fff", fontSize: "var(--text-xs)", fontWeight: 700 }}
                      >
                        <Monitor size={14} color="#fff" strokeWidth={2} />
                        Start Sharing
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Real-time overlay: Attention + Mood */}
            <div className="absolute bottom-[var(--sp-md)] right-[var(--sp-md)] pointer-events-none">
              <div
                className="p-[var(--sp-sm)] rounded-lg border shadow-xl flex items-center gap-[var(--sp-md)]"
                style={{ background: "rgba(255,255,255,0.9)", backdropFilter: "blur(8px)", borderColor: "var(--color-surface-highest)" }}
              >
                <div className="text-center">
                  <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-on-surface-variant)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Attention</div>
                  <div style={{ fontSize: "var(--text-h2)", fontWeight: 700, color: "var(--color-btn-action)" }}>{rtAttention}</div>
                </div>
                <div className="w-px h-8" style={{ background: "var(--color-surface-highest)" }} />
                <div className="text-center">
                  <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-on-surface-variant)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Mood</div>
                  <div style={{ fontSize: "var(--text-h2)", fontWeight: 700, color: "var(--color-secondary)" }}>{rtMood}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Share / Re-share button */}
          <div className="flex items-center px-[var(--sp-sm)]">
            {/* Button is clickable when idle or denied (not while actively sharing), and only if settings are configured */}
            {(() => {
              const canClick = shareStatus !== "active" && !recordPaused && settingsReady;
              const isActive = shareStatus === "active" || recordPaused;
              return (
                <button
                  onClick={canClick ? retryShare : undefined}
                  disabled={isActive || !settingsReady}
                  title={
                    !settingsReady
                      ? "Configure Project Settings first"
                      : shareStatus === "denied"
                      ? "Try again"
                      : hasSharedBefore
                      ? "Share screen again"
                      : "Start screen share"
                  }
                  className="p-[var(--sp-sm)] rounded-lg border transition-colors"
                  style={{
                    background: canClick ? "rgba(255,255,255,0.85)" : "rgba(255,255,255,0.4)",
                    backdropFilter: "blur(8px)",
                    borderColor: shareStatus === "denied" && settingsReady
                      ? "var(--color-error)"
                      : "var(--color-outline-variant)",
                    cursor: canClick ? "pointer" : "not-allowed",
                    opacity: canClick ? 1 : 0.4,
                  }}
                  onMouseEnter={(e) => {
                    if (!canClick) return;
                    (e.currentTarget as HTMLElement).style.borderColor = "var(--color-btn-action)";
                    (e.currentTarget as HTMLElement).style.background = "rgba(0,120,212,0.08)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.borderColor =
                      shareStatus === "denied" && settingsReady ? "var(--color-error)" : "var(--color-outline-variant)";
                    (e.currentTarget as HTMLElement).style.background = canClick
                      ? "rgba(255,255,255,0.85)"
                      : "rgba(255,255,255,0.4)";
                  }}
                >
                  {hasSharedBefore
                    ? <RotateCcw size={20} color={canClick ? "#404752" : "#9ca3af"} strokeWidth={2} />
                    : <Airplay size={20} color={canClick ? (shareStatus === "denied" ? "var(--color-error)" : "#404752") : "#9ca3af"} />}
                </button>
              );
            })()}
          </div>
        </div>

        {/* Pause / Resume / Stop bar */}
        {(shareStatus === "active" || recordPaused) && (
          <div
            className="px-[var(--sp-md)] py-[var(--sp-sm)] border-t flex items-center gap-[var(--sp-sm)]"
            style={{ borderColor: "var(--color-surface-highest)", background: "var(--color-surface-low)" }}
          >
            <button
              onClick={recordPaused ? resumeStream : pauseStream}
              className="flex items-center gap-[var(--sp-xs)] px-[var(--sp-md)] py-[var(--sp-xs)] rounded-lg border transition-colors"
              style={{ background: "var(--color-surface-bright)", borderColor: "var(--color-outline-variant)", fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--color-on-surface)" }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(0,120,212,0.08)"; (e.currentTarget as HTMLElement).style.borderColor = "var(--color-btn-action)"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "var(--color-surface-bright)"; (e.currentTarget as HTMLElement).style.borderColor = "var(--color-outline-variant)"; }}
            >
              {recordPaused ? <Play size={16} color="#0078d4" strokeWidth={2} /> : <Pause size={16} color="#0078d4" strokeWidth={2} />}
              <span>{recordPaused ? "Resume" : "Pause"}</span>
            </button>
            <button
              onClick={stopStream}
              className="flex items-center gap-[var(--sp-xs)] px-[var(--sp-md)] py-[var(--sp-xs)] rounded-lg border transition-colors"
              style={{ background: "var(--color-surface-bright)", borderColor: "var(--color-outline-variant)", fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--color-error)" }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(186,26,26,0.08)"; (e.currentTarget as HTMLElement).style.borderColor = "var(--color-error)"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "var(--color-surface-bright)"; (e.currentTarget as HTMLElement).style.borderColor = "var(--color-outline-variant)"; }}
            >
              <PlayCircle size={16} color="var(--color-error)" strokeWidth={2} />
              <span>Stop</span>
            </button>
          </div>
        )}
      </section>

      {/* ── Instruction panel ── */}
      <section
        className="rounded-lg border overflow-hidden shadow-sm"
        style={{ background: "var(--color-surface-lowest)", borderColor: "var(--color-surface-highest)" }}
      >
        {/* Header */}
        <div
          className="px-[var(--sp-md)] py-[var(--sp-sm)] border-b flex items-center justify-between"
          style={{ background: "var(--color-surface-low)", borderColor: "var(--color-surface-highest)" }}
        >
          <div className="flex items-center gap-[var(--sp-sm)]">
            <Bot size={16} color="#0078d4" strokeWidth={2} />
            <span style={{ fontSize: "var(--text-xs)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--color-on-surface-variant)" }}>
              AI Instruction
            </span>
          </div>
          <span style={{ fontSize: 10, color: "var(--color-on-surface-variant)", opacity: 0.7 }}>
            {sessionConfig.audienceAmount ? `${audienceDisplay} audience` : "Configure audience in Project Settings"}
          </span>
        </div>

        {/* Body */}
        <div className="p-[var(--sp-md)] flex flex-col gap-[var(--sp-sm)]">
          <p style={{ fontSize: "var(--text-sm)", color: "var(--color-on-surface-variant)", lineHeight: "var(--lh-sm)", fontStyle: "italic" }}>
            Describe what feedback you need. The AI will analyze your screen content and voice against your Project Settings.
          </p>

          {/* Input row */}
          <div
            className="flex items-center gap-[var(--sp-sm)] rounded-lg border px-[var(--sp-md)] py-[var(--sp-sm)]"
            style={{ background: "#fff", borderColor: "var(--color-outline-variant)" }}
          >
            <input
              type="text"
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              onKeyDown={handleInstructionKey}
              placeholder="e.g. 'Focus on whether my technical explanation is clear for a non-technical audience'"
              disabled={instructionSending}
              className="flex-1 bg-transparent border-none p-0 focus:ring-0 text-[length:var(--text-body)]"
              style={{ color: "var(--color-on-surface)", outline: "none" }}
            />
            <button
              onClick={sendInstruction}
              disabled={!instruction.trim() || instructionSending}
              className="flex items-center gap-[var(--sp-xs)] px-[var(--sp-md)] py-[var(--sp-xs)] rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              style={{ background: "var(--color-btn-action)", color: "#fff", fontSize: "var(--text-xs)", fontWeight: 600 }}
            >
              <Send size={14} strokeWidth={2} />
              <span>{instructionSending ? "Sending…" : "Send"}</span>
            </button>
          </div>

          {/* Voice indicator */}
          {shareStatus === "active" && (
            <div className="flex items-center gap-[var(--sp-xs)]">
              <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: "#c4362c" }} />
              <span style={{ fontSize: 10, color: "var(--color-on-surface-variant)", fontWeight: 600 }}>
                Voice detection active — speech is captured and sent to AI
              </span>
            </div>
          )}
        </div>
      </section>

      {/* ── 4 metric cards ── */}
      <div className="grid grid-cols-4 gap-[var(--sp-md)]">
        {/* Live Audience */}
        <div className="bg-white border rounded-lg p-[var(--sp-md)] shadow-sm flex flex-col" style={{ borderColor: "var(--color-surface-highest)" }}>
          <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--color-on-surface-variant)" }}>
            Live Audience
          </span>
          <div style={{ fontSize: "var(--text-h2)", fontWeight: 700, color: "var(--color-on-surface)" }}>
            {audienceDisplay}
          </div>
          <span style={{ fontSize: 9, color: "var(--color-on-surface-variant)", marginTop: 2 }}>from settings</span>
        </div>

        {/* Complexity */}
        <div className="bg-white border rounded-lg p-[var(--sp-md)] shadow-sm flex flex-col" style={{ borderColor: "var(--color-surface-highest)" }}>
          <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--color-on-surface-variant)" }}>
            Complexity
          </span>
          <div style={{ fontSize: "var(--text-h2)", fontWeight: 700, color: cxColor }}>
            {dispComplexity}
          </div>
          <span style={{ fontSize: 9, color: "var(--color-on-surface-variant)", marginTop: 2 }}>after session</span>
        </div>

        {/* Attention */}
        <div className="bg-white border rounded-lg p-[var(--sp-md)] shadow-sm flex flex-col" style={{ borderColor: "var(--color-surface-highest)" }}>
          <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--color-on-surface-variant)" }}>
            Attention
          </span>
          <div style={{ fontSize: "var(--text-h2)", fontWeight: 700, color: "var(--color-btn-action)" }}>
            {dispAttention}
          </div>
          <span style={{ fontSize: 9, color: "var(--color-on-surface-variant)", marginTop: 2 }}>after session</span>
        </div>

        {/* Mood */}
        <div className="bg-white border rounded-lg p-[var(--sp-md)] shadow-sm flex flex-col" style={{ borderColor: "var(--color-surface-highest)" }}>
          <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--color-on-surface-variant)" }}>
            Mood
          </span>
          <div style={{ fontSize: "var(--text-h2)", fontWeight: 700, color: mdColor }}>
            {dispMood}
          </div>
          <span style={{ fontSize: 9, color: "var(--color-on-surface-variant)", marginTop: 2 }}>after session</span>
        </div>
      </div>

      {/* ── Questions card ── */}
      <div
        className="bg-white border rounded-lg p-[var(--sp-md)] shadow-sm"
        style={{ borderColor: "var(--color-surface-highest)" }}
      >
        <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--color-on-surface-variant)" }}>
          Questions
        </span>
        {dispQuestions.length === 0 ? (
          <div style={{ fontSize: "var(--text-h2)", fontWeight: 700, color: "var(--color-on-surface)", marginTop: 4 }}>--</div>
        ) : (
          <ul className="mt-[var(--sp-sm)] flex flex-col gap-[var(--sp-xs)]">
            {dispQuestions.map((q, i) => (
              <li key={i} className="flex items-start gap-[var(--sp-sm)]">
                <span
                  className="rounded px-[var(--sp-xs)] flex-shrink-0"
                  style={{ fontSize: 9, fontWeight: 800, background: "rgba(0,120,212,0.10)", color: "var(--color-btn-action)", padding: "2px 6px", marginTop: 2 }}
                >
                  Q{i + 1}
                </span>
                <span style={{ fontSize: "var(--text-sm)", color: "var(--color-on-surface)", lineHeight: "var(--lh-sm)" }}>{q}</span>
              </li>
            ))}
          </ul>
        )}
        <p style={{ fontSize: 9, color: "var(--color-on-surface-variant)", marginTop: 6 }}>
          Questions the audience may ask after your presentation — populated after session ends.
        </p>
      </div>

      {/* ── Graph panel ── */}
      {aliveDocAnalysis && (
        <div style={{ height: 400 }}>
          <AnalysisGraphPanel data={aliveDocAnalysis} />
        </div>
      )}
    </div>
  );
}
