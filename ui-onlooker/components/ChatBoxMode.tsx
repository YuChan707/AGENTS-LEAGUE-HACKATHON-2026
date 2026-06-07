"use client";

import { useState, useRef, useEffect } from "react";
import { User, BotSquare, File as FileIcon, Bot } from "@deemlol/next-icons";

interface Message {
  id: number;
  role: "user" | "bot";
  text: string;
}

interface ChatBoxModeProps {
  onSessionChange?: (active: boolean) => void;
}

export default function ChatBoxMode({ onSessionChange }: ChatBoxModeProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 0,
      role: "bot",
      text: "Hello! I'm your OnLooker AI assistant. Upload a file or ask me anything about your presentation.",
    },
  ]);
  const [input, setInput] = useState("");
  const [botTyping, setBotTyping] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, botTyping]);

  const sendMessage = () => {
    const text = input.trim();
    if (!text) return;

    onSessionChange?.(true);
    const userMsg: Message = { id: Date.now(), role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setBotTyping(true);

    setTimeout(() => {
      setBotTyping(false);
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, role: "bot", text: "Hi." },
      ]);
    }, 800);
  };

  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files ?? []);
    setAttachedFiles((prev) => {
      const merged = [...prev, ...selected].slice(0, 3);
      if (merged.length > 0) onSessionChange?.(true);
      return merged;
    });
    e.target.value = "";
  };

  const removeFile = (index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const atLimit = attachedFiles.length >= 3;

  return (
    <section
      className="fl-card w-full flex flex-col overflow-hidden"
      style={{ height: "100%", minHeight: 480 }}
    >
      {/* Header */}
      <div
        className="px-[var(--sp-md)] py-[var(--sp-sm)] border-b flex items-center justify-between bg-white"
        style={{ borderColor: "var(--color-outline-variant)" }}
      >
        <div className="flex items-center gap-[var(--sp-sm)]">
          <Bot size={22} color="#0078d4" strokeWidth={2} />
          <span
            style={{
              fontSize: "var(--text-xs)",
              fontWeight: 600,
              color: "var(--color-on-surface-variant)",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            Chat Box — AI Audience Feedback
          </span>
        </div>
        {/* File type tags */}
        <div className="flex gap-[var(--sp-xs)]">
          {[".pptx", ".docx", ".pdf"].map((ext) => (
            <span
              key={ext}
              className="rounded px-[var(--sp-xs)]"
              style={{
                fontSize: 10,
                fontWeight: 600,
                textTransform: "uppercase",
                background: "var(--color-surface-high)",
                color: "var(--color-on-surface-variant)",
                padding: "2px 6px",
              }}
            >
              {ext}
            </span>
          ))}
        </div>
      </div>

      {/* Messages area */}
      <div
        className="flex-1 overflow-y-auto no-scrollbar p-[var(--sp-lg)] flex flex-col gap-[var(--sp-md)]"
        style={{ background: "var(--color-surface-low)" }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-end gap-[var(--sp-sm)] ${
              msg.role === "user" ? "flex-row-reverse" : "flex-row"
            }`}
          >
            {/* Avatar */}
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden"
              style={{
                background:
                  msg.role === "bot"
                    ? "var(--color-btn-action)"
                    : "var(--color-surface-low)",
                border:
                  msg.role === "user"
                    ? "1.5px solid var(--color-outline-variant)"
                    : "none",
              }}
            >
              {msg.role === "bot" ? (
                <BotSquare size={20} color="#ffffff" strokeWidth={2} />
              ) : (
                <User size={20} color="#0078d4" strokeWidth={2} />
              )}
            </div>

            {/* Bubble */}
            <div
              className="max-w-[72%] px-[var(--sp-md)] py-[var(--sp-sm)] rounded-lg"
              style={{
                background:
                  msg.role === "user"
                    ? "var(--color-btn-action)"
                    : "var(--color-surface-bright)",
                color:
                  msg.role === "user"
                    ? "#ffffff"
                    : "var(--color-on-surface)",
                border:
                  msg.role === "bot"
                    ? "1px solid var(--color-outline-variant)"
                    : "none",
                fontSize: "var(--text-body)",
                lineHeight: "var(--lh-body)",
                boxShadow: "var(--shadow-soft)",
              }}
            >
              {msg.text}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {botTyping && (
          <div className="flex items-end gap-[var(--sp-sm)]">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden"
              style={{ background: "var(--color-btn-action)" }}
            >
              <BotSquare size={20} color="#FFFFFF" strokeWidth={2} />
            </div>
            <div
              className="px-[var(--sp-md)] py-[var(--sp-sm)] rounded-lg flex items-center gap-1 border"
              style={{
                background: "var(--color-surface-bright)",
                borderColor: "var(--color-outline-variant)",
                boxShadow: "var(--shadow-soft)",
              }}
            >
              <div className="w-1.5 h-1.5 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
              <div className="w-1.5 h-1.5 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
              <div className="w-1.5 h-1.5 rounded-full dot-pulse" style={{ background: "var(--color-btn-action)" }} />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Attached files strip */}
      {attachedFiles.length > 0 && (
        <div
          className="px-[var(--sp-md)] py-[var(--sp-xs)] flex flex-wrap gap-[var(--sp-xs)] border-t"
          style={{ borderColor: "var(--color-outline-variant)", background: "var(--color-surface-low)" }}
        >
          {attachedFiles.map((f, i) => (
            <div
              key={i}
              className="flex items-center gap-[var(--sp-xs)] rounded border px-[var(--sp-xs)] py-[2px]"
              style={{
                background: "var(--color-surface-bright)",
                borderColor: "var(--color-outline-variant)",
                fontSize: "var(--text-xs)",
                color: "var(--color-on-surface-variant)",
                maxWidth: 180,
              }}
            >
              <FileIcon size={12} color="#0078d4" strokeWidth={2} />
              <span className="truncate flex-1" style={{ maxWidth: 120 }}>{f.name}</span>
              <button
                onClick={() => removeFile(i)}
                style={{ color: "var(--color-on-surface-variant)", lineHeight: 1, fontWeight: 700, fontSize: 14 }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--color-error)")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--color-on-surface-variant)")}
              >
                ×
              </button>
            </div>
          ))}
          <span style={{ fontSize: "var(--text-xs)", color: "var(--color-on-surface-variant)", alignSelf: "center", opacity: 0.6 }}>
            {attachedFiles.length}/3
          </span>
        </div>
      )}

      {/* Input bar */}
      <div
        className="px-[var(--sp-md)] py-[var(--sp-sm)] border-t flex items-center gap-[var(--sp-sm)] bg-white"
        style={{ borderColor: "var(--color-outline-variant)" }}
      >
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pptx,.docx,.pdf"
          style={{ display: "none" }}
          onChange={handleFileSelect}
        />

        {/* Attach button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={atLimit}
          className="flex items-center justify-center w-8 h-8 rounded transition-colors"
          title={atLimit ? "Maximum 3 files reached" : "Attach file (.pptx, .docx, .pdf)"}
          style={{ color: atLimit ? "var(--color-outline-variant)" : "var(--color-on-surface-variant)", opacity: atLimit ? 0.5 : 1 }}
        >
          <FileIcon size={20} color={atLimit ? "#c0c7d4" : "#0078d4"} strokeWidth={2} />
        </button>

        {/* Text input */}
        <div className="fl-input flex-1">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask about your presentation or paste a question..."
            className="bg-transparent border-none p-0 pb-[var(--sp-xs)] focus:ring-0 w-full text-[length:var(--text-body)]"
            style={{ color: "var(--color-on-surface)", outline: "none" }}
            disabled={botTyping}
          />
        </div>

        {/* Send button */}
        <button
          onClick={sendMessage}
          disabled={!input.trim() || botTyping}
          className="fl-btn-primary px-[var(--sp-md)] py-[var(--sp-xs)] flex items-center gap-[var(--sp-xs)] disabled:opacity-40 disabled:cursor-not-allowed"
          style={{ borderRadius: "var(--br-sm)" }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>send</span>
          <span style={{ fontSize: "var(--text-body)", fontWeight: 600 }}>Send</span>
        </button>
      </div>
    </section>
  );
}
