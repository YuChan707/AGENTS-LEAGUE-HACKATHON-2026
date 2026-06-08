"use client";

import { useState } from "react";
import { useStore } from "@/lib/store";

const API_BASE =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) ||
  "http://localhost:8000";

const LOGO_B64 =
  "data:image/png;base64,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";

// Map UI audience type → backend persona_type
function toPersonaType(audience: string): string {
  if (audience === "Business") return "executive";
  if (audience === "Academic") return "executive";
  if (audience === "Student") return "customer";
  return "customer";
}

// Map location text → backend region code
function toRegion(location: string): string {
  const l = location.toLowerCase();
  if (l.includes("japan") || l.includes("tokyo") || l === "jp") return "jp";
  if (l.includes("uk") || l.includes("london") || l.includes("cambridge") || l.includes("england")) return "uk";
  if (l.includes("germany") || l.includes("berlin") || l === "de") return "de";
  return "us";
}

// Map Area dropdown → backend focus_area
function toFocusArea(area: string): string {
  const map: Record<string, string> = {
    Sciences: "science",
    Technology: "technology",
    Healthcare: "healthcare",
    Research: "research",
    Organization: "business",
  };
  return map[area] ?? "business";
}

interface ProjectSettingsProps {
  mode?: "dashboard" | "analysis";
  showUpdateButton?: boolean;
  onUpdate?: () => void;
}

export default function ProjectSettings({
  mode = "analysis",
  showUpdateButton = true,
  onUpdate,
}: ProjectSettingsProps) {
  const btnLabel = mode === "dashboard" ? "Save Configuration" : "Update";
  const setSessionConfig = useStore((s) => s.setSessionConfig);
  const setSessionId = useStore((s) => s.setSessionId);

  const [audience, setAudience] = useState("");
  const [environment, setEnvironment] = useState("");
  const [complexity, setComplexity] = useState("");
  const [area, setArea] = useState("");
  const [location, setLocation] = useState("");
  const [focusPeople, setFocusPeople] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setError(null);
    const personaType = toPersonaType(audience);
    const region = toRegion(location);
    const focusArea = toFocusArea(area);

    // Update store config immediately so WS init message uses these values
    setSessionConfig({ personaType, region, focusArea });

    setLoading(true);
    try {
      const params = new URLSearchParams({ persona_type: personaType, region, focus_area: focusArea });
      const res = await fetch(`${API_BASE}/session/start?${params}`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setSessionId(data.session_id);
      }
    } catch {
      setError("Backend unreachable — running in offline mode.");
    } finally {
      setLoading(false);
    }

    onUpdate?.();
  };

  return (
    <section className="flex flex-col gap-[var(--sp-sm)]">
      <div className="flex items-center justify-between mb-[var(--sp-sm)]">
        <h2 style={{ fontSize: "var(--text-h2)", fontWeight: 600, color: "var(--color-on-surface)" }}>
          Project Settings
        </h2>
      </div>

      <div className="fl-card p-[var(--sp-lg)] flex flex-col gap-[var(--sp-lg)]">
        {/* Type of Audience */}
        <div className="flex flex-col gap-[var(--sp-xs)]">
          <FieldLabel>Type of audience</FieldLabel>
          <div className="fl-input">
            <select
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              className="bg-transparent border-none p-0 pb-[var(--sp-xs)] focus:ring-0 w-full appearance-none cursor-pointer text-[length:var(--text-body)]"
              style={{ color: "var(--color-on-surface)" }}
            >
              <option value="" disabled>--</option>
              <option>Business</option>
              <option>Academic</option>
              <option>Student</option>
              <option>Casual (common people)</option>
            </select>
          </div>
        </div>

        {/* Environment */}
        <div className="flex flex-col gap-[var(--sp-xs)]">
          <FieldLabel>Environment</FieldLabel>
          <div className="fl-input">
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="bg-transparent border-none p-0 pb-[var(--sp-xs)] focus:ring-0 w-full appearance-none cursor-pointer text-[length:var(--text-body)]"
              style={{ color: "var(--color-on-surface)" }}
            >
              <option value="" disabled>--</option>
              <option>Casual presentation</option>
              <option>Professional presentation</option>
            </select>
          </div>
        </div>

        {/* Complexity */}
        <div className="flex flex-col gap-[var(--sp-xs)]">
          <FieldLabel>Complexity</FieldLabel>
          <div className="fl-input">
            <select
              value={complexity}
              onChange={(e) => setComplexity(e.target.value)}
              className="bg-transparent border-none p-0 pb-[var(--sp-xs)] focus:ring-0 w-full appearance-none cursor-pointer text-[length:var(--text-body)]"
              style={{ color: "var(--color-on-surface)" }}
            >
              <option value="" disabled>--</option>
              <option>Low level</option>
              <option>Medium level</option>
              <option>High level</option>
            </select>
          </div>
        </div>

        {/* Area */}
        <div className="flex flex-col gap-[var(--sp-xs)]">
          <FieldLabel>Area (Optional)</FieldLabel>
          <div className="fl-input">
            <select
              value={area}
              onChange={(e) => setArea(e.target.value)}
              className="bg-transparent border-none p-0 pb-[var(--sp-xs)] focus:ring-0 w-full appearance-none cursor-pointer text-[length:var(--text-body)]"
              style={{ color: "var(--color-on-surface)" }}
            >
              <option value="" disabled>--</option>
              <option>Sciences</option>
              <option>Technology</option>
              <option>Healthcare</option>
              <option>Research</option>
              <option>Organization</option>
            </select>
          </div>
        </div>

        {/* Location */}
        <div className="flex flex-col gap-[var(--sp-xs)]">
          <FieldLabel>Location</FieldLabel>
          <div className="fl-input">
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Cambridge, UK"
              className="bg-transparent border-none p-0 pb-[var(--sp-xs)] focus:ring-0 w-full text-[length:var(--text-body)]"
              style={{ color: "var(--color-on-surface-variant)" }}
            />
          </div>
        </div>

        {/* Focus People (dashboard only) */}
        {mode === "dashboard" && (
          <div className="flex flex-col gap-[var(--sp-xs)]">
            <FieldLabel>Focus people</FieldLabel>
            <div className="fl-input">
              <input
                type="text"
                value={focusPeople}
                onChange={(e) => setFocusPeople(e.target.value)}
                placeholder="e.g. Mixed Global"
                className="bg-transparent border-none p-0 pb-[var(--sp-xs)] focus:ring-0 w-full text-[length:var(--text-body)]"
                style={{ color: "var(--color-on-surface)" }}
              />
            </div>
          </div>
        )}

        {error && (
          <p style={{ fontSize: "var(--text-xs)", color: "var(--color-error)" }}>{error}</p>
        )}

        {showUpdateButton && (
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="fl-btn-primary mt-[var(--sp-md)] w-full py-[var(--sp-sm)] shadow-sm uppercase tracking-widest disabled:opacity-50"
          >
            {loading ? "Saving…" : btnLabel}
          </button>
        )}
      </div>
    </section>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label
      style={{
        fontSize: "var(--text-xs)",
        fontWeight: 600,
        color: "var(--color-on-surface-variant)",
        textTransform: "uppercase",
        letterSpacing: "0.08em",
      }}
    >
      {children}
    </label>
  );
}
