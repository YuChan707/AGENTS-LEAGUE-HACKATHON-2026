"use client";

import { Files } from "lucide-react";
import { useStore } from "@/lib/store";

export default function DocumentsPanel() {
  const fileQueue = useStore((s) => s.fileQueue);
  const dequeueFile = useStore((s) => s.dequeueFile);

  if (fileQueue.length === 0) return null;

  return (
    <section
      className="rounded-lg overflow-hidden shadow-sm border"
      style={{ background: "var(--color-surface-lowest)", borderColor: "var(--color-outline-variant)" }}
    >
      {/* Header */}
      <div
        className="px-[var(--sp-md)] py-[var(--sp-sm)] border-b flex items-center gap-[var(--sp-sm)]"
        style={{ background: "var(--color-surface-low)", borderColor: "var(--color-outline-variant)" }}
      >
        <Files size={14} color="#0078d4" strokeWidth={2} />
        <span
          style={{
            fontSize: "var(--text-xs)",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            color: "var(--color-on-surface-variant)",
          }}
        >
          Documents
        </span>
        <span
          className="ml-auto rounded-full px-[var(--sp-xs)]"
          style={{
            fontSize: 10,
            fontWeight: 700,
            background: "var(--color-btn-action)",
            color: "#fff",
            minWidth: 18,
            textAlign: "center",
          }}
        >
          {fileQueue.length}
        </span>
      </div>

      {/* File rows */}
      <ul className="flex flex-col">
        {fileQueue.map((item, idx) => {
          const slot = idx + 1;
          const ext = item.name.includes(".") ? item.name.split(".").pop()?.toUpperCase() : "";
          const baseName = item.name.replace(/\.[^/.]+$/, "");
          return (
            <li
              key={item.uid}
              className="flex items-center gap-[var(--sp-sm)] px-[var(--sp-md)] py-[var(--sp-sm)] border-b last:border-b-0"
              style={{ borderColor: "var(--color-outline-variant)" }}
            >
              {/* Slot badge */}
              <span
                className="rounded flex items-center justify-center flex-shrink-0"
                style={{
                  width: 22,
                  height: 22,
                  background: "var(--color-btn-action)",
                  color: "#fff",
                  fontSize: 11,
                  fontWeight: 800,
                  fontFamily: "monospace",
                }}
              >
                {slot}
              </span>

              {/* Ext badge */}
              <span
                className="rounded px-[4px] flex-shrink-0"
                style={{
                  fontSize: 9,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  background: "var(--color-surface-high)",
                  color: "var(--color-on-surface-variant)",
                  padding: "1px 5px",
                }}
              >
                {ext}
              </span>

              {/* Filename */}
              <span
                className="flex-1 truncate"
                style={{
                  fontSize: "var(--text-xs)",
                  color: "var(--color-on-surface)",
                  fontWeight: 500,
                  minWidth: 0,
                }}
                title={item.name}
              >
                {baseName}
              </span>

              {/* Delete */}
              <button
                onClick={() => dequeueFile(item.uid)}
                className="flex-shrink-0 rounded flex items-center justify-center transition-colors"
                style={{
                  width: 20,
                  height: 20,
                  fontSize: 14,
                  fontWeight: 700,
                  lineHeight: 1,
                  color: "var(--color-on-surface-variant)",
                }}
                title={`Remove [${slot}] ${item.name}`}
                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--color-error)")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--color-on-surface-variant)")}
              >
                ×
              </button>
            </li>
          );
        })}
      </ul>

      {/* Capacity bar */}
      <div
        className="px-[var(--sp-md)] py-[var(--sp-xs)] flex items-center gap-[var(--sp-xs)]"
        style={{ background: "var(--color-surface-low)", borderTop: "1px solid var(--color-outline-variant)" }}
      >
        {[1, 2, 3].map((slot) => (
          <div
            key={slot}
            className="flex-1 h-1 rounded-full transition-all"
            style={{
              background: slot <= fileQueue.length ? "var(--color-btn-action)" : "var(--color-surface-high)",
            }}
          />
        ))}
        <span
          style={{
            fontSize: 10,
            color: fileQueue.length >= 3 ? "var(--color-error)" : "var(--color-on-surface-variant)",
            fontWeight: 600,
            marginLeft: 4,
          }}
        >
          {fileQueue.length}/3
        </span>
      </div>
    </section>
  );
}
