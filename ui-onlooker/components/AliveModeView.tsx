"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Monitor, RotateCcw, Pause, Play, PlayCircle } from "@deemlol/next-icons";

const LIVE_FEED = [
  { color: "var(--color-btn-action)",   text: "Audience engagement is peaking. Keep this pace." },
  { color: "var(--color-on-surface)",   text: "Someone mentioned the data source is unclear." },
  { color: "var(--color-secondary)",    text: "Attention dropping in the front rows. Use a gesture." },
  { color: "var(--color-btn-action)",   text: "Great point about the methodology!" },
  { color: "var(--color-btn-action)",   text: "Audience engagement is peaking. Keep this pace." },
];

export interface LiveMetrics {
  attention: string;
  mood: string;
  liveAudience: string;
  questions: string;
  complexity: string;
}

const DEFAULT_METRICS: LiveMetrics = {
  attention: "--",
  mood: "--",
  liveAudience: "--",
  questions: "--",
  complexity: "--",
};

interface AliveModeViewProps {
  onShareError?: () => void;
  onShareStatusChange?: (status: "idle" | "active" | "denied" | "paused") => void;
  metrics?: Partial<LiveMetrics>;
}

export default function AliveModeView({ onShareError, onShareStatusChange, metrics }: AliveModeViewProps) {
  const m: LiveMetrics = { ...DEFAULT_METRICS, ...metrics };
  const [shareStatus, setShareStatus] = useState<"idle" | "active" | "denied">("idle");
  const streamRef = useRef<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const hasRequestedRef = useRef(false);
  const [recordPaused, setRecordPaused] = useState(false);

  const requestShare = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true,
      });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      setShareStatus("active");
      onShareStatusChange?.("active");

      stream.getTracks()[0].addEventListener("ended", () => {
        setShareStatus("idle");
        onShareStatusChange?.("idle");
        streamRef.current = null;
        if (videoRef.current) videoRef.current.srcObject = null;
      });
    } catch {
      setShareStatus("denied");
      onShareStatusChange?.("denied");
      onShareError?.();
    }
  }, [onShareError, onShareStatusChange]);

  useEffect(() => {
    if (hasRequestedRef.current) return;
    hasRequestedRef.current = true;
    requestShare();
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, [requestShare]);

  const retryShare = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setShareStatus("idle");
    setRecordPaused(false);
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
    onShareStatusChange?.("idle");
  }, [onShareStatusChange]);

  return (
    <div className="flex flex-col gap-[var(--sp-lg)] flex-1">
      {/* Main live workspace */}
      <section
        className="bg-white border rounded-xl flex flex-col relative overflow-hidden shadow-lg"
        style={{ aspectRatio: "16/9", borderColor: "var(--color-surface-highest)" }}
      >
        {/* Background dot grid */}
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
            <span
              style={{
                fontSize: "var(--text-xs)",
                fontWeight: 700,
                color: "var(--color-on-surface-variant)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Live Stream: "--"
            </span>
          </div>
          <div className="flex items-center gap-[var(--sp-sm)]">
            <div
              className="flex items-center gap-[var(--sp-xs)] px-[var(--sp-sm)] py-[var(--sp-xs)] rounded"
              style={{ background: "rgba(186,26,26,0.1)", color: "var(--color-error)" }}
            >
              <div
                className="w-2 h-2 rounded-full animate-pulse"
                style={{ background: "var(--color-error)" }}
              />
              <span style={{ fontSize: 10, fontWeight: 700 }}>LIVE</span>
            </div>
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
        <div
          className="flex-1 flex relative overflow-hidden"
          style={{ background: "var(--color-surface-container)" }}
        >
          {/* Floating AI feedback bar */}
          <div
            className="absolute z-20 pointer-events-none"
            style={{ top: "var(--sp-md)", left: "50%", transform: "translateX(-50%)", width: "75%", maxWidth: 480 }}
          >
            <div
              className="flex items-center gap-[var(--sp-md)] p-[var(--sp-md)] rounded-xl border shadow-2xl"
              style={{
                background: "rgba(255,255,255,0.9)",
                backdropFilter: "blur(12px)",
                borderColor: "var(--color-surface-highest)",
              }}
            >
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm"
                style={{ background: "var(--color-btn-action)" }}
              >
                <span className="material-symbols-outlined" style={{ color: "#fff", fontSize: 20 }}>
                  auto_awesome
                </span>
              </div>
              <div className="overflow-hidden h-6 flex-1">
                <div className="scroll-feed flex flex-col gap-2">
                  {[...LIVE_FEED, ...LIVE_FEED].map((item, i) => (
                    <p
                      key={i}
                      style={{ fontSize: "var(--text-body)", fontWeight: 500, color: item.color, whiteSpace: "nowrap" }}
                    >
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
            {/* Shared screen window */}
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
                <div
                  className="ml-4"
                  style={{ fontSize: 10, color: "var(--color-on-surface-variant)", fontFamily: "monospace" }}
                >
                  https://research-slides.app/project-v2
                </div>
              </div>

              {/* Live video stream */}
              {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
              <video
                ref={videoRef}
                autoPlay
                muted
                style={{
                  display: shareStatus === "active" ? "block" : "none",
                  position: "absolute",
                  top: 32,
                  left: 0,
                  width: "100%",
                  height: "calc(100% - 32px)",
                  objectFit: "contain",
                  background: "#000",
                }}
              />

              {/* Placeholder (shown when no active stream) */}
              <div
                className="mt-8 h-full flex flex-col items-center justify-center gap-[var(--sp-md)]"
                style={{ background: "var(--color-surface-container)", display: shareStatus !== "active" ? "flex" : "none" }}
              >
                {shareStatus === "denied" ? (
                  <div
                    className="flex items-center gap-[var(--sp-sm)] px-[var(--sp-md)] py-[var(--sp-sm)] rounded-lg"
                    style={{ background: "var(--color-error-container)", color: "var(--color-error)" }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: 18 }}>warning</span>
                    <span style={{ fontSize: "var(--text-sm)" }}>Screen share was denied.</span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-[var(--sp-sm)]" style={{ color: "var(--color-on-surface-variant)" }}>
                    <Monitor size={32} color="#c0c7d4" strokeWidth={1.5} />
                    <span style={{ fontSize: "var(--text-sm)" }}>Waiting for screen share…</span>
                  </div>
                )}
              </div>
            </div>

            {/* Quick metrics overlay */}
            <div className="absolute bottom-[var(--sp-md)] right-[var(--sp-md)] pointer-events-none">
              <div
                className="p-[var(--sp-sm)] rounded-lg border shadow-xl flex items-center gap-[var(--sp-md)]"
                style={{
                  background: "rgba(255,255,255,0.9)",
                  backdropFilter: "blur(8px)",
                  borderColor: "var(--color-surface-highest)",
                }}
              >
                <div className="text-center">
                  <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-on-surface-variant)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Attention</div>
                  <div style={{ fontSize: "var(--text-h2)", fontWeight: 700, color: "var(--color-btn-action)" }}>{m.attention}</div>
                </div>
                <div className="w-px h-8" style={{ background: "var(--color-surface-highest)" }} />
                <div className="text-center">
                  <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-on-surface-variant)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Mood</div>
                  <div style={{ fontSize: "var(--text-h2)", fontWeight: 700, color: "var(--color-secondary)" }}>{m.mood}</div>
                </div>
              </div>
            </div>
          </div>

          {/* RotateCcw re-request button */}
          <div className="flex items-center px-[var(--sp-sm)]">
            <button
              onClick={retryShare}
              disabled={shareStatus !== "idle"}
              title="Re-request screen share"
              className="p-[var(--sp-sm)] rounded-lg border transition-colors"
              style={{
                background: shareStatus === "idle" ? "rgba(255,255,255,0.85)" : "rgba(255,255,255,0.4)",
                backdropFilter: "blur(8px)",
                borderColor: "var(--color-outline-variant)",
                cursor: shareStatus === "idle" ? "pointer" : "not-allowed",
                opacity: shareStatus === "idle" ? 1 : 0.4,
              }}
              onMouseEnter={(e) => {
                if (shareStatus === "idle") {
                  (e.currentTarget as HTMLElement).style.borderColor = "var(--color-btn-action)";
                  (e.currentTarget as HTMLElement).style.background = "rgba(0,120,212,0.08)";
                }
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.borderColor = "var(--color-outline-variant)";
                (e.currentTarget as HTMLElement).style.background = shareStatus === "idle" ? "rgba(255,255,255,0.85)" : "rgba(255,255,255,0.4)";
              }}
            >
              <RotateCcw size={20} color="#404752" strokeWidth={2} />
            </button>
          </div>
        </div>

        {/* Pause / Resume / Stop control bar */}
        {shareStatus === "active" || recordPaused ? (
          <div
            className="px-[var(--sp-md)] py-[var(--sp-sm)] border-t flex items-center gap-[var(--sp-sm)]"
            style={{ borderColor: "var(--color-surface-highest)", background: "var(--color-surface-low)" }}
          >
            {/* Pause / Resume toggle */}
            <button
              onClick={recordPaused ? resumeStream : pauseStream}
              className="flex items-center gap-[var(--sp-xs)] px-[var(--sp-md)] py-[var(--sp-xs)] rounded-lg border transition-colors"
              style={{
                background: "var(--color-surface-bright)",
                borderColor: "var(--color-outline-variant)",
                fontSize: "var(--text-xs)",
                fontWeight: 600,
                color: "var(--color-on-surface)",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.background = "rgba(0,120,212,0.08)";
                (e.currentTarget as HTMLElement).style.borderColor = "var(--color-btn-action)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.background = "var(--color-surface-bright)";
                (e.currentTarget as HTMLElement).style.borderColor = "var(--color-outline-variant)";
              }}
            >
              {recordPaused ? (
                <Play size={16} color="#0078d4" strokeWidth={2} />
              ) : (
                <Pause size={16} color="#0078d4" strokeWidth={2} />
              )}
              <span>{recordPaused ? "Resume" : "Pause"}</span>
            </button>

            {/* Stop button */}
            <button
              onClick={stopStream}
              className="flex items-center gap-[var(--sp-xs)] px-[var(--sp-md)] py-[var(--sp-xs)] rounded-lg border transition-colors"
              style={{
                background: "var(--color-surface-bright)",
                borderColor: "var(--color-outline-variant)",
                fontSize: "var(--text-xs)",
                fontWeight: 600,
                color: "var(--color-error)",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.background = "rgba(186,26,26,0.08)";
                (e.currentTarget as HTMLElement).style.borderColor = "var(--color-error)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.background = "var(--color-surface-bright)";
                (e.currentTarget as HTMLElement).style.borderColor = "var(--color-outline-variant)";
              }}
            >
              <PlayCircle size={16} color="var(--color-error)" strokeWidth={2} />
              <span>Stop</span>
            </button>
          </div>
        ) : null}
      </section>

      {/* Insights summary row */}
      <div className="grid grid-cols-3 gap-[var(--sp-md)]">
        {[
          { label: "Live Audience", value: m.liveAudience },
          { label: "Questions",     value: m.questions },
          { label: "Complexity",    value: m.complexity, valueColor: "var(--color-tertiary)" },
        ].map(({ label, value, valueColor }) => (
          <div
            key={label}
            className="bg-white border rounded-lg p-[var(--sp-md)] shadow-sm flex flex-col"
            style={{ borderColor: "var(--color-surface-highest)" }}
          >
            <span
              style={{
                fontSize: 10,
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                color: "var(--color-on-surface-variant)",
              }}
            >
              {label}
            </span>
            <div
              style={{
                fontSize: "var(--text-h2)",
                fontWeight: 700,
                color: valueColor ?? "var(--color-on-surface)",
              }}
            >
              {value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
