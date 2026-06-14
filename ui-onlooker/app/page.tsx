"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import ProjectSettings from "@/components/ProjectSettings";
import DashboardView from "@/components/DashboardView";
import ChatBoxMode from "@/components/ChatBoxMode";
import AliveModeView from "@/components/AliveModeView";
import { Monitor, User, Feather, Bot } from "lucide-react";
import { useStore, CoachingPayload, AudiencePayload, AgentEvent, LiveAIInsight } from "@/lib/store";
import DocumentsPanel from "@/components/DocumentsPanel";

/* ── Logo ── */
const LOGO_SRC =
  "data:image/png;base64,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";

type View = "dashboard" | "analysis";
type Mode = "chat" | "alive";

export default function Page() {
  const [view, setView] = useState<View>("analysis");
  const [mode, setMode] = useState<Mode>("chat");
  const [shareState, setShareState] = useState<"idle" | "active" | "paused" | "denied">("idle");
  const [chatActive, setChatActive] = useState(false);
  const switchMode = (next: Mode) => setMode(next);


  return (
    <div
      className="flex flex-col min-h-screen"
      style={{ background: "var(--color-bg)", color: "var(--color-on-surface)" }}
    >
      {/* ── Header ── */}
      <header
        className="fixed top-0 w-full z-50 flex justify-between items-center px-[var(--sp-lg)] py-[var(--sp-sm)] border-b bg-white shadow-sm"
        style={{ borderColor: "var(--color-outline-variant)" }}
      >
        <div className="flex items-center gap-[var(--sp-md)]">
          <Image src={LOGO_SRC} alt="OnLooker logo" width={32} height={32} unoptimized />
          <span style={{ fontSize: "var(--text-h2)", fontWeight: 700, color: "var(--color-btn-action)" }}>
            OnLooker AI
          </span>
        </div>

        <div className="hidden md:flex items-center gap-[var(--sp-lg)]">
          <nav className="flex gap-[var(--sp-md)]">
            <div className="relative group">
              <button
                onClick={() => setView("dashboard")}
                className="px-[var(--sp-md)] py-[var(--sp-sm)] rounded transition-colors text-[length:var(--text-body)]"
                style={
                  view === "dashboard"
                    ? { color: "var(--color-btn-action)", fontWeight: 600, borderBottom: "2px solid var(--color-btn-action)" }
                    : { color: "var(--color-on-surface)" }
                }
              >
                Dashboard
              </button>
              <div
                className="absolute left-1/2 -translate-x-1/2 top-full mt-2 px-[var(--sp-sm)] py-[var(--sp-xs)] rounded shadow-lg pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap"
                style={{
                  background: "var(--color-inverse-surface)",
                  color: "var(--color-inverse-on-surface)",
                  fontSize: "var(--text-xs)",
                  zIndex: 100,
                }}
              >
                This section is under maintenance.
                <div
                  className="absolute left-1/2 -translate-x-1/2 -translate-y-1 top-0"
                  style={{
                    borderLeft: "5px solid transparent",
                    borderRight: "5px solid transparent",
                    borderBottom: "5px solid var(--color-inverse-surface)",
                  }}
                />
              </div>
            </div>

            <button
              onClick={() => setView("analysis")}
              className="px-[var(--sp-md)] py-[var(--sp-sm)] rounded transition-colors text-[length:var(--text-body)]"
              style={
                view === "analysis"
                  ? { color: "var(--color-btn-action)", fontWeight: 600, borderBottom: "2px solid var(--color-btn-action)" }
                  : { color: "var(--color-on-surface)" }
              }
            >
              Analysis
            </button>
          </nav>

          <div className="flex gap-[var(--sp-sm)]">
            <div className="relative group">
              <button
                className="p-[var(--sp-xs)] rounded transition-colors font-bold"
                style={{ color: "var(--color-on-surface-variant)", fontSize: "var(--text-body)", lineHeight: 1, width: 28, height: 28 }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--color-btn-action)")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--color-on-surface-variant)")}
              >
                ?
              </button>
              <div
                className="absolute right-0 top-full mt-2 px-[var(--sp-sm)] py-[var(--sp-xs)] rounded shadow-lg pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap"
                style={{ background: "var(--color-inverse-surface)", color: "var(--color-inverse-on-surface)", fontSize: "var(--text-xs)", zIndex: 100 }}
              >
                this is disable
              </div>
            </div>
            <div className="relative group">
              <button
                className="p-[var(--sp-xs)] rounded transition-colors flex items-center justify-center"
                style={{ color: "var(--color-on-surface-variant)", width: 28, height: 28 }}
              >
                <User size={20} color="#404752" strokeWidth={2} />
              </button>
              <div
                className="absolute right-0 top-full mt-2 px-[var(--sp-sm)] py-[var(--sp-xs)] rounded shadow-lg pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap"
                style={{ background: "var(--color-inverse-surface)", color: "var(--color-inverse-on-surface)", fontSize: "var(--text-xs)", zIndex: 100 }}
              >
                this is disable
              </div>
            </div>
          </div>
        </div>
      </header>

      <main
        className="flex-1 pt-20 px-[var(--sp-lg)] pb-40 flex flex-col md:flex-row gap-[var(--sp-lg)] max-w-[1440px] mx-auto w-full"
      >
        {view === "dashboard" && (
          <>
            <div className="w-full md:w-1/3 flex flex-col gap-[var(--sp-lg)]">
              <ProjectSettings mode="dashboard" />
              <section className="fl-card overflow-hidden">
                <div
                  className="px-[var(--sp-md)] py-[var(--sp-xs)] border-b flex items-center gap-[var(--sp-sm)]"
                  style={{ background: "var(--color-surface-container)", borderColor: "var(--color-outline-variant)" }}
                >
                  <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: "#107c10" }} />
                  <span style={{ fontSize: "var(--text-xs)", fontWeight: 700, textTransform: "uppercase", color: "var(--color-on-surface-variant)", letterSpacing: "0.06em" }}>
                    AI Preview Instance
                  </span>
                </div>
                <div className="p-[var(--sp-lg)] flex flex-col gap-[var(--sp-md)]">
                  <div className="flex items-start gap-[var(--sp-md)]">
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center"
                      style={{ background: "var(--color-surface-container)" }}
                    >
                      <Feather size={20} color="#404752" strokeWidth={2} />
                    </div>
                    <div
                      className="p-[var(--sp-md)] rounded max-w-[80%] border"
                      style={{ background: "var(--color-surface-low)", borderColor: "rgba(192,199,212,0.3)" }}
                    >
                      <p style={{ fontSize: "var(--text-body)", color: "var(--color-on-surface)" }}>
                        AI Audience Member{" "}
                        <span style={{ color: "var(--color-on-surface-variant)", opacity: 0.6, fontStyle: "italic", marginLeft: 4 }}>
                          typing...
                        </span>
                      </p>
                      <div className="flex gap-1 mt-[var(--sp-xs)]">
                        <div className="w-1.5 h-1.5 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
                        <div className="w-1.5 h-1.5 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
                        <div className="w-1.5 h-1.5 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
                      </div>
                    </div>
                  </div>
                </div>
              </section>
            </div>
            <div className="flex-1">
              <DashboardView />
            </div>
          </>
        )}

        {view === "analysis" && (
          <>
            <div className="w-full md:w-1/3 flex flex-col gap-[var(--sp-lg)]">
              <DocumentsPanel />
              <ProjectSettings mode="analysis" />
              <LiveAIPanel
                mode={mode}
                isLive={mode === "alive" ? (shareState === "active" || shareState === "paused") : chatActive}
                isPaused={mode === "alive" && shareState === "paused"}
              />
            </div>
            <div className="flex-1 flex flex-col gap-[var(--sp-lg)]">
              <div style={{ display: mode === "chat" ? "flex" : "none", flexDirection: "column", flex: 1 }}>
                <ChatBoxMode onSessionChange={(active) => setChatActive(active)} />
              </div>
              <div style={{ display: mode === "alive" ? "flex" : "none", flexDirection: "column", flex: 1 }}>
                <AliveModeView onShareStatusChange={(s) => setShareState(s)} />
              </div>
            </div>
          </>
        )}
      </main>

      {view === "analysis" && (
        <div
          className="fixed bottom-0 left-0 w-full z-40 flex flex-col items-center gap-[var(--sp-sm)] border-t py-[var(--sp-md)] px-[var(--sp-xl)]"
          style={{
            background: "var(--color-surface-lowest)",
            borderColor: "var(--color-surface-highest)",
            boxShadow: "var(--shadow-up)",
            borderRadius: "12px 12px 0 0",
          }}
        >
          <div className="flex gap-[var(--sp-lg)] w-full max-w-4xl justify-center">
            <ModeCard
              active={mode === "chat"}
              icon="chat"
              iconNode={<Bot size={20} color={mode === "chat" ? "#0078d4" : "#404752"} strokeWidth={2} />}
              label="Chat box"
              sub="Upload files & chat with AI"
              tooltip="Send your document to get feedback."
              tags={[".pptx", ".docx", ".pdf"]}
              onClick={() => switchMode("chat")}
            />
            <ModeCard
              active={mode === "alive"}
              icon="screenshot_monitor"
              iconNode={<Monitor size={20} color={mode === "alive" ? "#0078d4" : "#404752"} strokeWidth={2} />}
              label="Alive mode"
              sub="Share your screen for live feedback"
              tooltip="Stop sharing screen"
              activeLabel="Active session"
              onClick={() => switchMode("alive")}
            />
          </div>
          <div
            className="flex items-center gap-[var(--sp-xs)] mt-[var(--sp-xs)]"
            style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "var(--color-on-surface-variant)", opacity: 0.6 }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>chevron_left</span>
            swipe to switch mode
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>chevron_right</span>
          </div>
        </div>
      )}
    </div>
  );
}

interface ModeCardProps {
  active: boolean;
  icon: string;
  iconNode?: React.ReactNode;
  label: string;
  sub: string;
  tooltip: string;
  tags?: string[];
  activeLabel?: string;
  onClick: () => void;
}

function ModeCard({ active, icon, iconNode, label, sub, tooltip, tags, activeLabel, onClick }: ModeCardProps) {
  return (
    <div
      className="relative flex-1 max-w-[340px] p-[var(--sp-md)] rounded-lg border cursor-pointer transition-all group"
      style={{
        background: "#ffffff",
        borderColor: "var(--color-outline-variant)",
        borderTop: active ? "3px solid var(--color-btn-action)" : "1px solid var(--color-outline-variant)",
        boxShadow: active ? "var(--shadow-card)" : "none",
        color: active ? "var(--color-on-surface)" : "var(--color-on-surface-variant)",
      }}
      onClick={onClick}
      onMouseEnter={(e) => {
        if (!active) (e.currentTarget as HTMLElement).style.background = "var(--color-surface-low)";
      }}
      onMouseLeave={(e) => {
        if (!active) (e.currentTarget as HTMLElement).style.background = "#ffffff";
      }}
    >
      <div
        className="absolute left-1/2 -translate-x-1/2 top-full mt-3 px-[var(--sp-md)] py-[var(--sp-sm)] rounded-lg pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap shadow-xl"
        style={{ background: "var(--color-inverse-surface)", color: "var(--color-inverse-on-surface)", fontSize: "var(--text-xs)", zIndex: 100 }}
      >
        {tooltip}
      </div>
      <div className="flex gap-[var(--sp-md)]">
        <div
          className="p-[var(--sp-sm)] rounded-lg flex items-center justify-center"
          style={{ background: active ? "rgba(0,120,212,0.1)" : "var(--color-surface-high)" }}
        >
          {iconNode ?? (
            <span
              className="material-symbols-outlined"
              style={{ fontSize: 20, color: active ? "var(--color-btn-action)" : "var(--color-on-surface-variant)", fontVariationSettings: active ? "'FILL' 1" : "'FILL' 0" }}
            >
              {icon}
            </span>
          )}
        </div>
        <div className="flex flex-col">
          <span style={{ fontSize: "var(--text-body)", fontWeight: active ? 700 : 400, color: active ? "var(--color-btn-action)" : "var(--color-on-surface)" }}>
            {label}
          </span>
          <span style={{ fontSize: 10, color: "var(--color-on-surface-variant)" }}>{sub}</span>
        </div>
      </div>
      {tags && (
        <div className="mt-[var(--sp-sm)] flex flex-wrap gap-[var(--sp-xs)]" style={{ opacity: active ? 1 : 0.6 }}>
          {tags.map((t) => (
            <span
              key={t}
              className="rounded px-1.5 py-[2px]"
              style={{ fontSize: 9, fontFamily: "monospace", fontWeight: 600, background: "var(--color-surface-highest)", color: "var(--color-on-surface-variant)" }}
            >
              {t}
            </span>
          ))}
        </div>
      )}
      {active && activeLabel && (
        <div className="mt-[var(--sp-sm)] flex items-center gap-[var(--sp-xs)]">
          <div className="flex-1 h-px" style={{ background: "rgba(0,120,212,0.1)" }} />
          <span style={{ fontSize: 9, fontWeight: 700, color: "var(--color-btn-action)", textTransform: "uppercase", letterSpacing: "0.1em" }}>
            {activeLabel}
          </span>
          <div className="flex-1 h-px" style={{ background: "rgba(0,120,212,0.1)" }} />
        </div>
      )}
    </div>
  );
}

function condenseFeedback(e: AgentEvent): string {
  if (e.agent === "coaching") {
    const tip = (e.payload as CoachingPayload).tip;
    // Already short — cap at first sentence
    return tip.split(/[.!?]/)[0].trim() || tip;
  }
  if (e.agent === "audience") {
    const p = e.payload as AudiencePayload;
    // One-sentence summary: reaction + body language
    const reaction = p.reaction_type.charAt(0).toUpperCase() + p.reaction_type.slice(1);
    return `${reaction} — ${p.body_language}`;
  }
  return "";
}

const INSIGHT_COLORS: Record<LiveAIInsight["category"], { bg: string; text: string; label: string }> = {
  grammar:    { bg: "rgba(245,158,11,0.12)",  text: "#b45309", label: "Grammar"    },
  engagement: { bg: "rgba(0,120,212,0.10)",   text: "#0078d4", label: "Engagement" },
  clarity:    { bg: "rgba(196,54,44,0.10)",   text: "#c4362c", label: "Clarity"    },
  structure:  { bg: "rgba(139,92,246,0.10)",  text: "#7c3aed", label: "Structure"  },
  delivery:   { bg: "rgba(16,124,16,0.10)",   text: "#107c10", label: "Delivery"   },
};

function LiveAIPanel({ mode, isLive, isPaused = false }: { mode: Mode; isLive: boolean; isPaused?: boolean }) {
  const endRef = useRef<HTMLDivElement>(null);
  const events = useStore((s) => s.events);
  const docAnalysis = useStore((s) => s.latestDocumentAnalysis);
  const filename = useStore((s) => s.latestFilename);
  const liveAIInsights = useStore((s) => s.liveAIInsights);

  const fileLabel = filename
    ? filename.length > 20 ? filename.slice(0, 18) + "…" : filename
    : null;

  const liveMessages = events
    .filter((e) => e.agent === "coaching" || e.agent === "audience")
    .map((e) => {
      const text = condenseFeedback(e);
      if (!text) return "";
      return fileLabel ? `${fileLabel} — ${text}` : text;
    })
    .filter(Boolean);

  const hasInsights = liveAIInsights.length > 0;
  const hasData = liveMessages.length > 0 || hasInsights;
  const dotColor = hasData ? "#107c10" : isLive ? "#f59e0b" : "#9ca3af";
  const statusLabel = hasData ? "Live AI Analysis" : isLive ? "AI Processing…" : "AI Inactive";

  const [elapsed, setElapsed] = useState(0);
  const isPausedRef = useRef(isPaused);
  useEffect(() => { isPausedRef.current = isPaused; }, [isPaused]);

  useEffect(() => {
    if (!isLive || mode !== "alive") return;
    const id = setInterval(() => {
      if (!isPausedRef.current) setElapsed((s) => s + 1);
    }, 1000);
    return () => { clearInterval(id); setElapsed(0); };
  }, [isLive, mode]);

  useEffect(() => {
    if (hasData) endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [hasData, liveMessages.length, hasInsights]);

  const hh = String(Math.floor(elapsed / 3600)).padStart(2, "0");
  const mm = String(Math.floor((elapsed % 3600) / 60)).padStart(2, "0");
  const ss = String(elapsed % 60).padStart(2, "0");
  const recTime = `${hh}:${mm}:${ss}`;

  return (
    <section
      className="rounded-lg overflow-hidden shadow-sm border"
      style={{ background: "var(--color-surface-lowest)", borderColor: "var(--color-surface-highest)" }}
    >
      {/* Header */}
      <div
        className="px-[var(--sp-md)] py-[var(--sp-sm)] border-b flex items-center justify-between"
        style={{ background: "var(--color-surface-low)", borderColor: "var(--color-surface-highest)" }}
      >
        <div className="flex items-center gap-[var(--sp-sm)]">
          <div
            className="w-2 h-2 rounded-full"
            style={{
              background: dotColor,
              animation: hasData || isLive ? "pulse 2s cubic-bezier(0.4,0,0.6,1) infinite" : "none",
            }}
          />
          <span style={{ fontSize: "var(--text-xs)", fontWeight: 700, textTransform: "uppercase", color: "var(--color-on-surface-variant)", letterSpacing: "0.06em" }}>
            {statusLabel}
          </span>
        </div>
        {isLive && mode === "alive" && (
          <span
            className="border rounded px-[var(--sp-xs)]"
            style={{ fontSize: 10, color: "var(--color-on-surface-variant)", borderColor: "var(--color-outline-variant)" }}
          >
            REC {recTime}
          </span>
        )}
      </div>

      {/* Body */}
      <div className="p-[var(--sp-md)] flex flex-col gap-[var(--sp-sm)]">

        {/* State 1: Inactive */}
        {!isLive && !hasData && (
          <div className="flex flex-col gap-[var(--sp-sm)]">
            <div className="flex items-start gap-[var(--sp-sm)]">
              <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: "var(--color-surface-high)" }}>
                <Feather size={12} color="#717783" strokeWidth={2} />
              </div>
              <div
                className="px-[var(--sp-sm)] py-[var(--sp-xs)] rounded-lg border"
                style={{ background: "var(--color-surface-low)", borderColor: "var(--color-surface-highest)", fontSize: "var(--text-sm)", color: "var(--color-on-surface-variant)", fontStyle: "italic", lineHeight: "var(--lh-sm)" }}
              >
                {mode === "alive" ? "Start screen sharing to activate live analysis." : "Send a message or upload a file to activate analysis."}
              </div>
            </div>
            {docAnalysis?.short_feedback && (
              <div className="flex items-start gap-[var(--sp-sm)]">
                <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: "rgba(0,120,212,0.12)" }}>
                  <Feather size={12} color="#0078d4" strokeWidth={2} />
                </div>
                <div
                  className="px-[var(--sp-sm)] py-[var(--sp-xs)] rounded-lg flex-1"
                  style={{ background: "rgba(0,120,212,0.04)", borderLeft: "2px solid var(--color-btn-action)", fontSize: "var(--text-sm)", color: "var(--color-on-surface)", lineHeight: "var(--lh-sm)", paddingLeft: 8 }}
                >
                  <span style={{ display: "block", fontSize: 9, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--color-btn-action)", marginBottom: 2 }}>
                    Reminder
                  </span>
                  {docAnalysis.short_feedback}
                </div>
              </div>
            )}
          </div>
        )}

        {/* State 2: Processing */}
        {isLive && !hasData && (
          <div className="flex items-start gap-[var(--sp-sm)]">
            <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: "var(--color-btn-action)" }}>
              <Feather size={12} color="#ffffff" strokeWidth={2} />
            </div>
            <div
              className="px-[var(--sp-sm)] py-[var(--sp-xs)] rounded-lg border flex items-center gap-[var(--sp-sm)]"
              style={{ background: "var(--color-surface-low)", borderColor: "var(--color-surface-highest)" }}
            >
              <span style={{ fontSize: "var(--text-sm)", color: "var(--color-on-surface-variant)", fontStyle: "italic" }}>
                Waiting for AI response…
              </span>
              <div className="flex gap-1">
                <div className="w-1 h-1 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
                <div className="w-1 h-1 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
                <div className="w-1 h-1 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
              </div>
            </div>
          </div>
        )}

        {/* State 3: Active — categorized insights + live session events */}
        {hasData && (
          <div className="overflow-y-auto no-scrollbar flex flex-col gap-[var(--sp-sm)]" style={{ maxHeight: 280 }}>

            {/* Document-derived categorized insights */}
            {hasInsights && liveAIInsights.map((item: LiveAIInsight, i: number) => {
              const c = INSIGHT_COLORS[item.category] ?? INSIGHT_COLORS.delivery;
              return (
                <div key={`insight-${i}`} className="flex items-start gap-[var(--sp-sm)]">
                  <span
                    className="rounded flex-shrink-0 flex items-center justify-center"
                    style={{
                      minWidth: 64,
                      fontSize: 9,
                      fontWeight: 800,
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                      background: c.bg,
                      color: c.text,
                      padding: "3px 6px",
                      borderRadius: 4,
                      lineHeight: 1.4,
                    }}
                  >
                    {c.label}
                  </span>
                  <div
                    className="flex-1 px-[var(--sp-sm)] py-[var(--sp-xs)] rounded-lg border"
                    style={{ background: "var(--color-surface-low)", borderColor: "var(--color-surface-highest)", fontSize: "var(--text-sm)", color: "var(--color-on-surface)", lineHeight: "var(--lh-sm)" }}
                  >
                    {item.text}
                  </div>
                </div>
              );
            })}

            {/* Live session events (coaching / audience) */}
            {liveMessages.map((msg: string, i: number) => {
              const sepIdx = msg.indexOf(" — ");
              const hasLabel = fileLabel && sepIdx !== -1 && msg.startsWith(fileLabel);
              const labelPart = hasLabel ? msg.slice(0, sepIdx) : null;
              const bodyPart = hasLabel ? msg.slice(sepIdx + 3) : msg;
              return (
                <div key={`live-${i}`} className="flex items-start gap-[var(--sp-sm)]">
                  <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: "var(--color-btn-action)" }}>
                    <Feather size={12} color="#ffffff" strokeWidth={2} />
                  </div>
                  <div
                    className="px-[var(--sp-sm)] py-[var(--sp-xs)] rounded-lg border flex-1"
                    style={{ background: "var(--color-surface-low)", borderColor: "var(--color-surface-highest)", fontSize: "var(--text-sm)", color: "var(--color-on-surface)", lineHeight: "var(--lh-sm)" }}
                  >
                    {labelPart && (
                      <span style={{ fontWeight: 700, color: "var(--color-btn-action)", marginRight: 4, fontSize: 10 }}>
                        [{labelPart}]
                      </span>
                    )}
                    {bodyPart}
                  </div>
                </div>
              );
            })}

            {isLive && (
              <div className="flex items-center gap-[var(--sp-sm)]">
                <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: "var(--color-btn-action)" }}>
                  <Feather size={12} color="#ffffff" strokeWidth={2} />
                </div>
                <div className="px-[var(--sp-sm)] py-[var(--sp-xs)] rounded-lg border flex gap-1 items-center" style={{ background: "var(--color-surface-low)", borderColor: "var(--color-surface-highest)" }}>
                  <div className="w-1 h-1 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
                  <div className="w-1 h-1 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
                  <div className="w-1 h-1 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>
        )}

      </div>
    </section>
  );
}
