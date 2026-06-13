"use client";

import { useState } from "react";
import { BarChart2, Users, TrendingUp, Zap } from "lucide-react";
import { DocumentAnalysisPayload, GraphGroup } from "@/lib/store";

interface Props {
  data: DocumentAnalysisPayload;
}

type GroupBy = "ages" | "type";
type Metric  = "engagement" | "impact";

const METRIC_META: Record<Metric, { label: string; color: string; bg: string; icon: React.ReactNode }> = {
  engagement: {
    label: "Audience Engagement",
    color: "#0078d4",
    bg: "rgba(0,120,212,0.12)",
    icon: <Zap size={13} strokeWidth={2.5} />,
  },
  impact: {
    label: "Impact (Understanding)",
    color: "#107c10",
    bg: "rgba(16,124,16,0.12)",
    icon: <TrendingUp size={13} strokeWidth={2.5} />,
  },
};

function Bar({ value, color, bg }: { value: number; color: string; bg: string }) {
  return (
    <div
      className="relative w-full rounded-sm overflow-hidden"
      style={{ height: 8, background: "var(--color-surface-high)" }}
    >
      <div
        className="absolute left-0 top-0 h-full rounded-sm transition-all duration-500"
        style={{ width: `${value}%`, background: color, boxShadow: `0 0 6px ${bg}` }}
      />
    </div>
  );
}

function GroupRow({ row, metric, color, bg }: { row: GraphGroup; metric: Metric; color: string; bg: string }) {
  const value = row[metric];
  return (
    <div className="flex flex-col gap-[3px]">
      <div className="flex items-center justify-between">
        <span style={{ fontSize: 11, fontWeight: 600, color: "var(--color-on-surface-variant)" }}>
          {row.group}
        </span>
        <span style={{ fontSize: 11, fontWeight: 700, color, minWidth: 32, textAlign: "right" }}>
          {value}%
        </span>
      </div>
      <Bar value={value} color={color} bg={bg} />
    </div>
  );
}

export default function AnalysisGraphPanel({ data }: Props) {
  const [groupBy, setGroupBy] = useState<GroupBy>("ages");
  const [metric, setMetric] = useState<Metric>("engagement");

  const rows: GraphGroup[] = groupBy === "ages" ? data.graph_data.by_age : data.graph_data.by_type;
  const { label, color, bg, icon } = METRIC_META[metric];

  // Average score for the selected metric
  const avg = Math.round(rows.reduce((s, r) => s + r[metric], 0) / rows.length);

  return (
    <div
      className="flex flex-col h-full overflow-hidden rounded-lg border"
      style={{
        background: "var(--color-surface-lowest)",
        borderColor: "var(--color-outline-variant)",
        minWidth: 0,
      }}
    >
      {/* ── Header ── */}
      <div
        className="px-[var(--sp-md)] py-[var(--sp-sm)] border-b flex items-center gap-[var(--sp-sm)]"
        style={{ background: "var(--color-surface-low)", borderColor: "var(--color-outline-variant)" }}
      >
        <BarChart2 size={16} color="#0078d4" strokeWidth={2} />
        <span
          style={{
            fontSize: "var(--text-xs)",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            color: "var(--color-on-surface-variant)",
          }}
        >
          Audience Insights
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-[var(--sp-md)] flex flex-col gap-[var(--sp-md)]">

        {/* ── Metric tabs ── */}
        <div className="flex gap-[var(--sp-xs)]">
          {(["engagement", "impact"] as Metric[]).map((m) => {
            const active = metric === m;
            const meta = METRIC_META[m];
            return (
              <button
                key={m}
                onClick={() => setMetric(m)}
                className="flex-1 flex items-center justify-center gap-1 py-[var(--sp-xs)] rounded-md border transition-all"
                style={{
                  fontSize: 11,
                  fontWeight: active ? 700 : 500,
                  background: active ? meta.bg : "transparent",
                  borderColor: active ? meta.color : "var(--color-outline-variant)",
                  color: active ? meta.color : "var(--color-on-surface-variant)",
                }}
              >
                {meta.icon}
                {m === "engagement" ? "Engage" : "Impact"}
              </button>
            );
          })}
        </div>

        {/* ── Group filter ── */}
        <div className="flex flex-col gap-[var(--sp-xs)]">
          <div className="flex items-center gap-[var(--sp-xs)]">
            <Users size={12} color="#717783" strokeWidth={2} />
            <span
              style={{
                fontSize: 10,
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                color: "var(--color-on-surface-variant)",
              }}
            >
              Group by
            </span>
          </div>
          <div className="flex gap-[var(--sp-xs)]">
            {(["ages", "type"] as GroupBy[]).map((g) => {
              const active = groupBy === g;
              return (
                <button
                  key={g}
                  onClick={() => setGroupBy(g)}
                  className="flex-1 py-[var(--sp-xs)] rounded border transition-all"
                  style={{
                    fontSize: 11,
                    fontWeight: active ? 700 : 400,
                    background: active ? "var(--color-btn-action)" : "transparent",
                    borderColor: active ? "var(--color-btn-action)" : "var(--color-outline-variant)",
                    color: active ? "#ffffff" : "var(--color-on-surface-variant)",
                  }}
                >
                  {g === "ages" ? "Ages" : "Type of People"}
                </button>
              );
            })}
          </div>
        </div>

        {/* ── Average score badge ── */}
        <div
          className="flex items-center justify-between rounded-lg px-[var(--sp-sm)] py-[var(--sp-xs)]"
          style={{ background: bg, border: `1px solid ${color}22` }}
        >
          <div className="flex items-center gap-[var(--sp-xs)]" style={{ color }}>
            {icon}
            <span style={{ fontSize: 11, fontWeight: 600 }}>{label}</span>
          </div>
          <span style={{ fontSize: 16, fontWeight: 800, color }}>{avg}%</span>
        </div>

        {/* ── Bars ── */}
        <div className="flex flex-col gap-[var(--sp-sm)]">
          {rows.map((row) => (
            <GroupRow key={row.group} row={row} metric={metric} color={color} bg={bg} />
          ))}
        </div>

        {/* ── Legend ── */}
        <div
          className="flex items-center gap-[var(--sp-xs)] pt-[var(--sp-xs)] border-t"
          style={{ borderColor: "var(--color-outline-variant)" }}
        >
          <div className="w-3 h-1.5 rounded-full" style={{ background: color }} />
          <span style={{ fontSize: 10, color: "var(--color-on-surface-variant)" }}>
            {label} by {groupBy === "ages" ? "age group" : "audience type"}
          </span>
        </div>

        {/* ── Short feedback ── */}
        {data.short_feedback && (
          <div
            className="rounded-lg p-[var(--sp-sm)] border-l-2 flex flex-col gap-[2px]"
            style={{
              background: "rgba(0,120,212,0.05)",
              borderLeftColor: "var(--color-btn-action)",
            }}
          >
            <span
              style={{
                fontSize: 9,
                fontWeight: 800,
                textTransform: "uppercase",
                letterSpacing: "0.1em",
                color: "var(--color-btn-action)",
              }}
            >
              Key Takeaway
            </span>
            <span style={{ fontSize: "var(--text-xs)", color: "var(--color-on-surface)", lineHeight: 1.4 }}>
              {data.short_feedback}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
