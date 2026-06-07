"use client";

export default function DashboardView() {
  return (
    <section
      className="fl-card w-full flex flex-col relative overflow-hidden"
      style={{ aspectRatio: "16/9" }}
    >
      {/* Panel header */}
      <div
        className="px-[var(--sp-md)] py-[var(--sp-sm)] border-b flex justify-between items-center bg-white"
        style={{ borderColor: "var(--color-outline-variant)" }}
      >
        <div className="flex items-center gap-[var(--sp-sm)]">
          <span
            className="material-symbols-outlined"
            style={{ color: "var(--color-btn-action)", fontSize: 22 }}
          >
            analytics
          </span>
          <span
            style={{
              fontSize: "var(--text-xs)",
              fontWeight: 600,
              color: "var(--color-on-surface-variant)",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            Audience Engagement Visualizer
          </span>
        </div>
        <div className="flex gap-[var(--sp-sm)]">
          <span
            className="material-symbols-outlined cursor-pointer transition-colors"
            style={{ color: "var(--color-on-surface-variant)", fontSize: 20 }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--color-btn-action)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--color-on-surface-variant)")}
          >
            fullscreen
          </span>
          <span
            className="material-symbols-outlined cursor-pointer transition-colors"
            style={{ color: "var(--color-on-surface-variant)", fontSize: 20 }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--color-btn-action)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--color-on-surface-variant)")}
          >
            refresh
          </span>
        </div>
      </div>

      {/* Grid workspace */}
      <div
        className="flex-1 p-[var(--sp-xl)]"
        style={{ background: "var(--color-surface-low)" }}
      >
        <div className="grid grid-cols-12 grid-rows-6 gap-[var(--sp-md)] w-full h-full">

          {/* Main chart – col 1-8, rows 1-4 */}
          <div
            className="col-span-8 row-span-4 border rounded overflow-hidden shadow-sm flex items-center justify-center group bg-white"
            style={{ borderColor: "var(--color-outline-variant)" }}
          >
            {/* Placeholder waveform chart */}
            <svg viewBox="0 0 600 220" className="w-full h-full opacity-80 group-hover:scale-105 transition-transform duration-700" preserveAspectRatio="xMidYMid slice">
              <defs>
                <linearGradient id="waveGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#0078d4" stopOpacity="0.5" />
                  <stop offset="100%" stopColor="#0078d4" stopOpacity="0.02" />
                </linearGradient>
              </defs>
              <rect width="600" height="220" fill="var(--color-surface-low)" />
              <path
                d="M0,160 C40,145 80,100 120,90 C160,80 200,110 240,95 C280,80 320,50 360,60 C400,70 440,120 480,105 C520,90 560,75 600,80 L600,220 L0,220 Z"
                fill="url(#waveGrad)"
              />
              <path
                d="M0,160 C40,145 80,100 120,90 C160,80 200,110 240,95 C280,80 320,50 360,60 C400,70 440,120 480,105 C520,90 560,75 600,80"
                fill="none"
                stroke="#0078d4"
                strokeWidth="2"
              />
              {/* Grid lines */}
              {[40, 80, 120, 160, 200].map((y) => (
                <line key={y} x1="0" y1={y} x2="600" y2={y} stroke="#e0e0e0" strokeWidth="0.5" />
              ))}
            </svg>
          </div>

          {/* Attention Span – col 9-12, rows 1-2 */}
          <div
            className="col-span-4 row-span-2 border rounded p-[var(--sp-md)] flex flex-col justify-between shadow-sm bg-white"
            style={{ borderColor: "var(--color-outline-variant)" }}
          >
            <span style={{ fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--color-on-surface-variant)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Attention Span
            </span>
            <div style={{ fontSize: 32, color: "var(--color-btn-action)", fontWeight: 300, lineHeight: 1 }}>
              84<span style={{ fontSize: 18 }}>%</span>
            </div>
            <div
              className="h-1 w-full rounded-full overflow-hidden"
              style={{ background: "var(--color-surface-high)" }}
            >
              <div
                className="h-full rounded-full"
                style={{ width: "84%", background: "var(--color-btn-action)" }}
              />
            </div>
          </div>

          {/* Complexity Score – col 9-12, rows 3-4 */}
          <div
            className="col-span-4 row-span-2 border rounded p-[var(--sp-md)] flex flex-col justify-between shadow-sm bg-white"
            style={{ borderColor: "var(--color-outline-variant)" }}
          >
            <span style={{ fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--color-on-surface-variant)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Complexity Score
            </span>
            <div style={{ fontSize: 24, color: "var(--color-tertiary)", fontWeight: 600, lineHeight: 1 }}>
              High
            </div>
            <div className="flex items-center gap-[var(--sp-xs)]" style={{ fontSize: "var(--text-xs)", color: "var(--color-on-surface-variant)" }}>
              <span className="material-symbols-outlined" style={{ fontSize: 14, color: "#d83b01" }}>warning</span>
              Simplify technical terms
            </div>
          </div>

          {/* Data Points – col 1-4, rows 5-6 */}
          <div
            className="col-span-4 row-span-2 border rounded p-[var(--sp-md)] flex items-center justify-center shadow-sm bg-white"
            style={{ borderColor: "var(--color-outline-variant)" }}
          >
            <div className="text-center">
              <div style={{ fontSize: 28, fontWeight: 300, color: "var(--color-btn-action)" }}>12.4k</div>
              <div style={{ fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--color-on-surface-variant)", textTransform: "uppercase" }}>Data Points</div>
            </div>
          </div>

          {/* Key Takeaways AI – col 5-12, rows 5-6 */}
          <div
            className="col-span-8 row-span-2 border rounded p-[var(--sp-md)] flex flex-col gap-[var(--sp-sm)] shadow-sm bg-white"
            style={{ borderColor: "var(--color-outline-variant)" }}
          >
            <div className="flex justify-between items-center">
              <span style={{ fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--color-on-surface-variant)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                Key Takeaways AI
              </span>
              <span className="material-symbols-outlined" style={{ color: "var(--color-btn-action)", fontSize: 16 }}>
                auto_awesome
              </span>
            </div>
            <ul
              className="list-disc list-inside space-y-1"
              style={{ fontSize: "var(--text-body)", color: "var(--color-on-surface)" }}
            >
              <li>The methodology section requires more visual clarity for students.</li>
              <li>Academic audience appreciates the detailed source citations.</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
