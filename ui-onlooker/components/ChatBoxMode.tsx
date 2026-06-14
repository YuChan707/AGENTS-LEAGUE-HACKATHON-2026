"use client";

import { useState, useRef, useEffect } from "react";
import {
  User, BotMessageSquare as BotSquare, File as FileIcon, Bot,
  FileText, RotateCcw, PresentationIcon, BookOpen,
} from "lucide-react";
import {
  useStore, AgentEvent, CoachingPayload,
  DocumentAnalysisPayload,
} from "@/lib/store";
import AnalysisGraphPanel from "@/components/AnalysisGraphPanel";

const API_BASE =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) ||
  "http://localhost:8000";

const GREETING: PlainMessage = {
  id: 0,
  kind: "plain",
  role: "bot",
  text: "Hello! I'm your OnLooker AI assistant. Attach files in the Documents panel or type your content to get analysis, engagement graphs, and coaching tips.",
};

// ── Message types ────────────────────────────────────────────────────────────
interface PlainMessage {
  id: number;
  kind: "plain";
  role: "user" | "bot";
  text: string;
}

interface AnalysisMessage {
  id: number;
  kind: "analysis";
  role: "bot";
  docSlot: number;
  filePrefix: string;
  analysis: DocumentAnalysisPayload;
  audienceLabel: string;
  environmentLabel: string;
  complexityLabel: string;
}

type Message = PlainMessage | AnalysisMessage;

// ── Helpers ──────────────────────────────────────────────────────────────────
function plain(role: "user" | "bot", text: string): PlainMessage {
  return { id: Date.now() + Math.random(), kind: "plain", role, text };
}

/** "Q4 Financial Summary Analysis.pptx" → "Q4 Financial Sum" */
function filePrefix(name: string): string {
  const base = name.replace(/\.[^/.]+$/, "");
  const words = base.split(/\s+/).slice(0, 3).join(" ");
  return words.length > 16 ? words.slice(0, 15) + "…" : words;
}

const COACHING_NOISE = ["lack of information", "need more context", "keep speaking", "speak more"];

function formatChunkEvent(event: AgentEvent): string {
  if (event.agent === "coaching") {
    const p = event.payload as CoachingPayload;
    if (p.error || !p.tip) return "";
    if (COACHING_NOISE.some((n) => p.tip.toLowerCase().startsWith(n))) return "";
    return p.tip;
  }
  // Audience persona simulations are not meaningful in chat context
  return "";
}

// ── Sub-components ───────────────────────────────────────────────────────────
const DOC_TYPE_META = {
  presentation: { label: "Presentation", Icon: PresentationIcon, note: "Keep it short and simple — audiences need key points, not details." },
  report:       { label: "Report",       Icon: BookOpen,          note: "Reports need data, numbers, and references to be credible." },
  other:        { label: "Document",     Icon: FileText,          note: "" },
};

const SCORE_COLOR = (n: number) => n >= 75 ? "#107c10" : n >= 50 ? "#f59e0b" : "#c4362c";

function StructuredAnalysisBubble({ msg }: { msg: AnalysisMessage }) {
  const { analysis, docSlot, filePrefix: prefix, audienceLabel, environmentLabel, complexityLabel } = msg;
  const meta = DOC_TYPE_META[analysis.doc_type] ?? DOC_TYPE_META.other;
  const { audience, environment, complexity } = analysis.success_scores;

  return (
    <div
      className="rounded-lg overflow-hidden border w-full"
      style={{ borderColor: "var(--color-outline-variant)", background: "var(--color-surface-bright)", boxShadow: "var(--shadow-soft)" }}
    >
      {/* Header row */}
      <div
        className="px-[var(--sp-md)] py-[var(--sp-sm)] flex items-center gap-[var(--sp-sm)] border-b"
        style={{ background: "rgba(0,120,212,0.06)", borderColor: "var(--color-outline-variant)" }}
      >
        <span
          style={{
            fontFamily: "monospace",
            fontSize: 12,
            fontWeight: 800,
            color: "var(--color-btn-action)",
            background: "rgba(0,120,212,0.12)",
            borderRadius: 4,
            padding: "1px 6px",
          }}
        >
          [{docSlot}]
        </span>
        <span style={{ fontSize: "var(--text-xs)", fontWeight: 700, color: "var(--color-btn-action)" }}>
          {prefix}
        </span>
        <span style={{ fontSize: "var(--text-xs)", color: "var(--color-on-surface-variant)", opacity: 0.6 }}>—</span>
        <meta.Icon size={12} color="#0078d4" strokeWidth={2} />
        <span style={{ fontSize: "var(--text-xs)", color: "var(--color-on-surface-variant)" }}>{meta.label}</span>
        <span
          className="ml-auto rounded px-[var(--sp-xs)]"
          style={{
            fontSize: 9,
            fontWeight: 700,
            textTransform: "uppercase",
            background: analysis.language_tone === "professional" ? "rgba(16,124,16,0.1)" : "rgba(245,158,11,0.1)",
            color: analysis.language_tone === "professional" ? "#107c10" : "#f59e0b",
            padding: "2px 6px",
          }}
        >
          {analysis.language_tone}
        </span>
      </div>

      <div className="p-[var(--sp-md)] flex flex-col gap-[var(--sp-md)]">
        {/* Doc type note */}
        {meta.note && (
          <p style={{ fontSize: "var(--text-xs)", color: "var(--color-on-surface-variant)", fontStyle: "italic", borderLeft: "2px solid var(--color-btn-action)", paddingLeft: 8 }}>
            {meta.note}
          </p>
        )}

        {/* Opening paragraph */}
        {analysis.paragraphs[0] && (
          <p style={{ fontSize: "var(--text-body)", color: "var(--color-on-surface)", lineHeight: "var(--lh-body)" }}>
            {analysis.paragraphs[0]}
          </p>
        )}

        {/* Success scores */}
        <div
          className="rounded-lg p-[var(--sp-sm)] flex flex-col gap-[var(--sp-sm)]"
          style={{ background: "var(--color-surface-low)", border: "1px solid var(--color-outline-variant)" }}
        >
          <span style={{ fontSize: 10, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--color-on-surface-variant)" }}>
            Setting fit
          </span>
          {[
            { label: audienceLabel || "Audience",    value: audience,    tag: "Type of Audience" },
            { label: environmentLabel || "Environment", value: environment, tag: "Environment" },
            { label: complexityLabel || "Complexity",  value: complexity,  tag: "Complexity" },
          ].map(({ label, value, tag }) => (
            <div key={tag} className="flex items-center gap-[var(--sp-sm)]">
              <span style={{ fontSize: 11, color: "var(--color-on-surface-variant)", width: 110, flexShrink: 0 }}>
                {tag}
                <span style={{ fontWeight: 600, color: "var(--color-on-surface)", marginLeft: 4 }}>
                  ({label})
                </span>
              </span>
              <div className="flex-1 h-2 rounded-full" style={{ background: "var(--color-surface-high)", minWidth: 0 }}>
                <div
                  className="h-2 rounded-full transition-all"
                  style={{ width: `${value}%`, background: SCORE_COLOR(value) }}
                />
              </div>
              <span style={{ fontSize: 12, fontWeight: 800, color: SCORE_COLOR(value), minWidth: 36, textAlign: "right" }}>
                {value}%
              </span>
            </div>
          ))}
        </div>

        {/* Closing paragraph */}
        {analysis.paragraphs[1] && (
          <p style={{ fontSize: "var(--text-body)", color: "var(--color-on-surface)", lineHeight: "var(--lh-body)" }}>
            {analysis.paragraphs[1]}
          </p>
        )}
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
interface ChatBoxModeProps {
  onSessionChange?: (active: boolean) => void;
}

export default function ChatBoxMode({ onSessionChange }: Readonly<ChatBoxModeProps>) {
  const [messages, setMessages] = useState<Message[]>([GREETING]);
  const [input, setInput] = useState("");
  const [botTyping, setBotTyping] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    sessionId, sessionConfig,
    addEvent, setDocumentAnalysis, addDocumentAnalysis, documentAnalyses,
    setFilename, setLiveAIInsights,
    fileQueue, enqueueFile, clearFileQueue,
  } = useStore();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, botTyping]);

  useEffect(() => {
    if (!fileError) return;
    const t = setTimeout(() => setFileError(null), 4000);
    return () => clearTimeout(t);
  }, [fileError]);

  function handleReset() {
    setMessages([GREETING]);
    clearFileQueue();
    setFileError(null);
    setInput("");
    setDocumentAnalysis(null);
    onSessionChange?.(false);
  }

  async function analyzeText(text: string) {
    setBotTyping(true);
    onSessionChange?.(true);
    try {
      const res = await fetch(`${API_BASE}/analyze/chunk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          session_id: sessionId ?? "chat",
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
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json() as { events: AgentEvent[] };
      const msgs: PlainMessage[] = [];
      for (const ev of data.events) {
        addEvent(ev.agent, ev.payload);
        const t = formatChunkEvent(ev);
        if (t) msgs.push(plain("bot", t));
      }
      if (msgs.length) setMessages((p) => [...p, ...msgs]);
    } catch {
      setMessages((p) => [...p, plain("bot", "⚠️ Could not reach the backend. Make sure it is running on port 8000.")]);
    } finally {
      setBotTyping(false);
    }
  }

  async function uploadAndAnalyze(item: { uid: number; name: string; file: File }, slotNumber: number) {
    setBotTyping(true);
    onSessionChange?.(true);
    setFilename(item.name);
    const prefix = filePrefix(item.name);

    setMessages((p) => [...p, plain("bot", `[${slotNumber}] ${prefix}… — Reading file…`)]);

    try {
      const form = new FormData();
      form.append("file", item.file);
      form.append("session_id", sessionId ?? "chat");
      form.append("persona_type", sessionConfig.personaType);
      form.append("region", sessionConfig.region);
      form.append("focus_area", sessionConfig.focusArea);
      form.append("environment", sessionConfig.environment);
      form.append("complexity", sessionConfig.complexity);
      form.append("feedback_setting", sessionConfig.feedbackSetting ?? "academic_us");
      form.append("audience_min_age", String(sessionConfig.audienceMinAge ?? 18));
      form.append("audience_max_age", String(sessionConfig.audienceMaxAge ?? 45));
      form.append("audience_amount", String(sessionConfig.audienceAmount ?? 100));
      form.append("analyze", "true");

      const res = await fetch(`${API_BASE}/document/upload`, { method: "POST", body: form });
      if (!res.ok) throw new Error(`${res.status}`);

      const data = await res.json() as {
        filename: string;
        word_count: number;
        events?: AgentEvent[];
        document_analysis?: DocumentAnalysisPayload;
      };

      // Chunk-level events → plain messages
      const chunkMsgs: PlainMessage[] = [];
      for (const ev of data.events ?? []) {
        addEvent(ev.agent, ev.payload);
        const t = formatChunkEvent(ev);
        if (t) chunkMsgs.push(plain("bot", t));
      }

      // Full document analysis → structured message
      if (data.document_analysis) {
        addDocumentAnalysis(item.name, data.document_analysis);
        if (data.document_analysis.live_ai_items?.length) {
          setLiveAIInsights(data.document_analysis.live_ai_items);
        }

        const analysisMsg: AnalysisMessage = {
          id: Date.now() + 1,
          kind: "analysis",
          role: "bot",
          docSlot: slotNumber,
          filePrefix: prefix,
          analysis: data.document_analysis,
          audienceLabel: sessionConfig.personaType,
          environmentLabel: sessionConfig.environment,
          complexityLabel: sessionConfig.complexity,
        };
        setMessages((p) => [...p, ...chunkMsgs, analysisMsg]);
      } else {
        setMessages((p) => [
          ...p,
          ...chunkMsgs,
          plain("bot", `[${slotNumber}] ${prefix} — Extracted ${data.word_count} words. No deep analysis returned.`),
        ]);
      }
    } catch {
      setMessages((p) => [...p, plain("bot", `⚠️ Failed to process [${slotNumber}] ${item.name}. Check the backend.`)]);
    } finally {
      setBotTyping(false);
    }
  }

  const sendMessage = () => {
    const text = input.trim();
    if (!text && fileQueue.length === 0) return;

    if (text) {
      setMessages((p) => [...p, plain("user", text)]);
      setInput("");
      analyzeText(text);
    }

    if (fileQueue.length > 0) {
      const items = [...fileQueue];
      clearFileQueue();
      items.forEach((item, idx) => uploadAndAnalyze(item, idx + 1));
    }
  };

  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); if (!sendBlocked && !botTyping) sendMessage(); }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const incoming = Array.from(e.target.files ?? []);
    e.target.value = "";
    const available = 3 - fileQueue.length;
    if (available <= 0) {
      setFileError("Maximum 3 files reached — click Reset to free slots.");
      return;
    }
    const toAdd = incoming.slice(0, available);
    toAdd.forEach((f) => enqueueFile(f));
    if (incoming.length > available) {
      setFileError(`Only ${available} slot${available !== 1 ? "s" : ""} free — ${incoming.length - available} file${incoming.length - available !== 1 ? "s" : ""} skipped.`);
    }
    if (toAdd.length > 0) onSessionChange?.(true);
  };

  const settingsReady = !!sessionId;
  const atLimit = fileQueue.length >= 3;
  const hasAnalysis = documentAnalyses.length > 0;
  const sendBlocked = fileQueue.length === 0 || !settingsReady;

  return (
    <section className="fl-card w-full flex overflow-hidden" style={{ height: "100%", minHeight: 480 }}>

      {/* ── Left: chat ── */}
      <div
        className="flex flex-col"
        style={{
          width: hasAnalysis ? "55%" : "100%",
          borderRight: hasAnalysis ? "1px solid var(--color-outline-variant)" : "none",
          transition: "width 0.3s ease",
          minWidth: 0,
        }}
      >
        {/* Header */}
        <div
          className="px-[var(--sp-md)] py-[var(--sp-sm)] border-b flex items-center justify-between bg-white"
          style={{ borderColor: "var(--color-outline-variant)" }}
        >
          <div className="flex items-center gap-[var(--sp-sm)]">
            <Bot size={22} color="#0078d4" strokeWidth={2} />
            <span style={{ fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--color-on-surface-variant)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Chat Box — AI Audience Feedback
            </span>
          </div>
          <button
            onClick={handleReset}
            className="flex items-center gap-[4px] rounded border px-[var(--sp-sm)] py-[3px] transition-colors"
            title="Clear chat + file queue — AI panel data is kept"
            style={{ fontSize: 11, fontWeight: 600, color: "var(--color-on-surface-variant)", borderColor: "var(--color-outline-variant)" }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--color-error)"; (e.currentTarget as HTMLElement).style.color = "var(--color-error)"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--color-outline-variant)"; (e.currentTarget as HTMLElement).style.color = "var(--color-on-surface-variant)"; }}
          >
            <RotateCcw size={12} strokeWidth={2.5} />
            Reset
          </button>
        </div>

        {/* File-limit banner */}
        {fileError && (
          <div
            className="px-[var(--sp-md)] py-[var(--sp-xs)] flex items-center justify-between gap-[var(--sp-sm)] border-b"
            style={{ background: "rgba(196,43,28,0.06)", borderColor: "rgba(196,43,28,0.2)" }}
          >
            <span style={{ fontSize: "var(--text-xs)", color: "var(--color-error)" }}>⚠ {fileError}</span>
            <button onClick={() => setFileError(null)} style={{ fontSize: 14, fontWeight: 700, color: "var(--color-error)", lineHeight: 1, flexShrink: 0 }}>×</button>
          </div>
        )}

        {/* Messages */}
        <div
          className="flex-1 overflow-y-auto no-scrollbar p-[var(--sp-lg)] flex flex-col gap-[var(--sp-md)]"
          style={{ background: "var(--color-surface-low)" }}
        >
          {messages.map((msg) => {
            if (msg.kind === "analysis") {
              return (
                <div key={msg.id} className="flex items-start gap-[var(--sp-sm)]">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: "var(--color-btn-action)" }}>
                    <FileText size={16} color="#fff" strokeWidth={2} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <StructuredAnalysisBubble msg={msg} />
                  </div>
                </div>
              );
            }
            return (
              <div key={msg.id} className={`flex items-end gap-[var(--sp-sm)] ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ background: msg.role === "bot" ? "var(--color-btn-action)" : "var(--color-surface-low)", border: msg.role === "user" ? "1.5px solid var(--color-outline-variant)" : "none" }}
                >
                  {msg.role === "bot"
                    ? <BotSquare size={20} color="#ffffff" strokeWidth={2} />
                    : <User size={20} color="#0078d4" strokeWidth={2} />}
                </div>
                <div
                  className="max-w-[72%] px-[var(--sp-md)] py-[var(--sp-sm)] rounded-lg"
                  style={{
                    background: msg.role === "user" ? "var(--color-btn-action)" : "var(--color-surface-bright)",
                    color: msg.role === "user" ? "#ffffff" : "var(--color-on-surface)",
                    border: msg.role === "bot" ? "1px solid var(--color-outline-variant)" : "none",
                    fontSize: "var(--text-body)",
                    lineHeight: "var(--lh-body)",
                    boxShadow: "var(--shadow-soft)",
                  }}
                >
                  {msg.text}
                </div>
              </div>
            );
          })}

          {botTyping && (
            <div className="flex items-end gap-[var(--sp-sm)]">
              <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: "var(--color-btn-action)" }}>
                <BotSquare size={20} color="#FFFFFF" strokeWidth={2} />
              </div>
              <div className="px-[var(--sp-md)] py-[var(--sp-sm)] rounded-lg flex items-center gap-1 border" style={{ background: "var(--color-surface-bright)", borderColor: "var(--color-outline-variant)" }}>
                <div className="w-1.5 h-1.5 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
                <div className="w-1.5 h-1.5 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
                <div className="w-1.5 h-1.5 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="px-[var(--sp-md)] py-[var(--sp-sm)] border-t flex items-center gap-[var(--sp-sm)] bg-white" style={{ borderColor: "var(--color-outline-variant)" }}>
          <input ref={fileInputRef} type="file" multiple accept=".pptx,.docx,.pdf" style={{ display: "none" }} onChange={handleFileSelect} />

          <button
            onClick={() => atLimit ? setFileError("Maximum 3 files — click Reset to free slots.") : fileInputRef.current?.click()}
            className="flex items-center justify-center w-8 h-8 rounded"
            title={atLimit ? "Maximum 3 files — click Reset" : "Attach file (.pptx, .docx, .pdf)"}
            style={{ opacity: atLimit ? 0.5 : 1 }}
          >
            <FileIcon size={20} color={atLimit ? "#c0c7d4" : "#0078d4"} strokeWidth={2} />
          </button>

          <div className="fl-input flex-1">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder={fileQueue.length > 0 ? `${fileQueue.length} file${fileQueue.length > 1 ? "s" : ""} queued — press Send to analyze` : "Ask about your presentation or paste a question…"}
              className="bg-transparent border-none p-0 pb-[var(--sp-xs)] focus:ring-0 w-full text-[length:var(--text-body)]"
              style={{ color: "var(--color-on-surface)", outline: "none" }}
              disabled={botTyping}
            />
          </div>

          <span
            title={sendBlocked && !botTyping ? "please finish set your audiences and document" : undefined}
            style={{ display: "inline-flex", cursor: sendBlocked && !botTyping ? "not-allowed" : "default" }}
          >
            <button
              onClick={sendMessage}
              disabled={sendBlocked || botTyping}
              className="fl-btn-primary px-[var(--sp-md)] py-[var(--sp-xs)] flex items-center gap-[var(--sp-xs)] disabled:opacity-40 disabled:cursor-not-allowed"
              style={{ borderRadius: "var(--br-sm)", pointerEvents: sendBlocked ? "none" : undefined }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>send</span>
              <span style={{ fontSize: "var(--text-body)", fontWeight: 600 }}>Send</span>
            </button>
          </span>
        </div>
      </div>

      {/* ── Right: graph panel ── */}
      {hasAnalysis && (
        <div className="flex flex-col" style={{ width: "45%", minWidth: 0 }}>
          <AnalysisGraphPanel entries={documentAnalyses} />
        </div>
      )}
    </section>
  );
}
