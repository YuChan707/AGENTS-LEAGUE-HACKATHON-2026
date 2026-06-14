"use client";

import { useState, KeyboardEvent } from "react";
import {
  FolderOpen,
  Search,
  Download,
  CheckCircle,
  XCircle,
  Loader2,
} from "lucide-react";
import { useStore, DocumentAnalysisPayload } from "@/lib/store";

const API_BASE =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) ||
  "http://localhost:8000";

interface FileInfo {
  name: string;
  size_kb: number;
  path: string;
  ext: string;
}

interface FileResult {
  filename: string;
  folder: string;
  status: "success" | "error";
  word_count?: number;
  analysis?: DocumentAnalysisPayload;
  error?: string;
}

interface ScanData {
  folder_name: string;
  folder_path: string;
  file_count: number;
  files: FileInfo[];
  error?: string;
}

interface IngestData {
  folder_name: string;
  folder_path: string;
  processed: number;
  errors: number;
  results: FileResult[];
  error?: string;
}

export default function FolderIngestor() {
  const [folderPath, setFolderPath] = useState("");
  const [scanData, setScanData] = useState<ScanData | null>(null);
  const [ingestData, setIngestData] = useState<IngestData | null>(null);
  const [scanning, setScanning] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const { sessionConfig, addDocumentAnalysis } = useStore();

  async function handleScan() {
    const path = folderPath.trim();
    if (!path) return;
    setScanning(true);
    setErr(null);
    setScanData(null);
    setIngestData(null);
    try {
      const res = await fetch(`${API_BASE}/folder/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_path: path }),
      });
      const data: ScanData = await res.json();
      if (data.error) { setErr(data.error); return; }
      setScanData(data);
    } catch {
      setErr("Backend unreachable — start it on port 8000.");
    } finally {
      setScanning(false);
    }
  }

  async function handleIngest() {
    const path = folderPath.trim();
    if (!path) return;
    setIngesting(true);
    setErr(null);
    setIngestData(null);
    try {
      const res = await fetch(`${API_BASE}/folder/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          folder_path: path,
          persona_type: sessionConfig.personaType,
          region: sessionConfig.region,
          focus_area: sessionConfig.focusArea,
          environment: sessionConfig.environment || "professional",
          complexity: sessionConfig.complexity || "medium",
          feedback_setting: sessionConfig.feedbackSetting || "academic_us",
          audience_min_age: sessionConfig.audienceMinAge ?? 18,
          audience_max_age: sessionConfig.audienceMaxAge ?? 45,
          audience_amount: sessionConfig.audienceAmount ?? 100,
        }),
      });
      const data: IngestData = await res.json();
      if (data.error) { setErr(data.error); return; }
      setIngestData(data);
      for (const r of data.results) {
        if (r.status === "success" && r.analysis) {
          addDocumentAnalysis(`${data.folder_name}/${r.filename}`, r.analysis);
        }
      }
    } catch {
      setErr("Backend unreachable — start it on port 8000.");
    } finally {
      setIngesting(false);
    }
  }

  const hasFiles = (scanData?.file_count ?? 0) > 0;
  const busy = scanning || ingesting;

  return (
    <section
      className="rounded-lg overflow-hidden shadow-sm border"
      style={{
        background: "var(--color-surface-lowest)",
        borderColor: "var(--color-outline-variant)",
      }}
    >
      {/* Header */}
      <div
        className="px-[var(--sp-md)] py-[var(--sp-sm)] border-b flex items-center gap-[var(--sp-sm)]"
        style={{
          background: "var(--color-surface-low)",
          borderColor: "var(--color-outline-variant)",
        }}
      >
        <FolderOpen size={14} color="#0078d4" strokeWidth={2} />
        <span
          style={{
            fontSize: "var(--text-xs)",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            color: "var(--color-on-surface-variant)",
          }}
        >
          Folder Ingestor
        </span>
        <span
          style={{
            marginLeft: "auto",
            fontSize: 9,
            fontWeight: 600,
            padding: "1px 6px",
            borderRadius: 99,
            background: "rgba(0,120,212,0.1)",
            color: "#0078d4",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
          }}
        >
          MCP
        </span>
      </div>

      {/* Body */}
      <div className="p-[var(--sp-md)] flex flex-col gap-[var(--sp-sm)]">
        {/* Path input row */}
        <div className="flex gap-[var(--sp-xs)]">
          <input
            type="text"
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
            onKeyDown={(e: KeyboardEvent<HTMLInputElement>) => {
              if (e.key === "Enter") handleScan();
            }}
            placeholder="C:\Users\…\Slides   or   ~/presentations"
            disabled={busy}
            className="flex-1 rounded border px-[var(--sp-sm)] py-[4px] focus:outline-none"
            style={{
              fontSize: 11,
              fontFamily: "monospace",
              color: "var(--color-on-surface)",
              background: "var(--color-surface-high)",
              borderColor: "var(--color-outline-variant)",
            }}
          />
          <button
            onClick={handleScan}
            disabled={!folderPath.trim() || busy}
            className="flex items-center gap-[var(--sp-xs)] px-[var(--sp-sm)] py-[4px] rounded border transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            style={{
              fontSize: 11,
              fontWeight: 600,
              borderColor: "var(--color-outline-variant)",
              color: "var(--color-btn-action)",
              background: "var(--color-surface-lowest)",
            }}
          >
            {scanning ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <Search size={12} strokeWidth={2} />
            )}
            Scan
          </button>
        </div>

        {/* Error */}
        {err && (
          <p style={{ fontSize: "var(--text-xs)", color: "var(--color-error)" }}>
            ⚠ {err}
          </p>
        )}

        {/* Scan result: file list */}
        {scanData && (
          <div className="flex flex-col gap-[var(--sp-xs)]">
            {/* Row: folder label + Ingest button */}
            <div className="flex items-center justify-between">
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  color: "var(--color-on-surface-variant)",
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                }}
              >
                {scanData.folder_name} — {scanData.file_count} file
                {scanData.file_count !== 1 ? "s" : ""}
              </span>
              {hasFiles && (
                <button
                  onClick={handleIngest}
                  disabled={ingesting}
                  className="flex items-center gap-[var(--sp-xs)] px-[var(--sp-sm)] py-[3px] rounded transition-colors disabled:opacity-50"
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    background: "var(--color-btn-action)",
                    color: "#fff",
                  }}
                >
                  {ingesting ? (
                    <Loader2 size={12} className="animate-spin" />
                  ) : (
                    <Download size={12} strokeWidth={2} />
                  )}
                  {ingesting ? "Ingesting…" : "Ingest All"}
                </button>
              )}
            </div>

            {scanData.files.length === 0 ? (
              <p
                style={{
                  fontSize: "var(--text-xs)",
                  color: "var(--color-on-surface-variant)",
                  fontStyle: "italic",
                }}
              >
                No PPTX, DOCX, or PDF files found.
              </p>
            ) : (
              <ul className="flex flex-col gap-[2px]">
                {scanData.files.map((f) => {
                  const result = ingestData?.results.find(
                    (r) => r.filename === f.name
                  );
                  return (
                    <li
                      key={f.name}
                      className="flex items-center gap-[var(--sp-xs)]"
                    >
                      {result ? (
                        result.status === "success" ? (
                          <CheckCircle size={11} color="#107c10" />
                        ) : (
                          <XCircle size={11} color="#c4362c" />
                        )
                      ) : ingesting ? (
                        <Loader2
                          size={11}
                          className="animate-spin"
                          style={{ color: "var(--color-btn-action)" }}
                        />
                      ) : (
                        <div
                          className="w-[11px] h-[11px] rounded-full border"
                          style={{ borderColor: "var(--color-outline-variant)" }}
                        />
                      )}
                      <span
                        className="flex-1 truncate"
                        title={f.name}
                        style={{
                          fontSize: 11,
                          color: "var(--color-on-surface)",
                          fontFamily: "monospace",
                        }}
                      >
                        {f.name}
                      </span>
                      <span
                        style={{
                          fontSize: 9,
                          color: "var(--color-on-surface-variant)",
                        }}
                      >
                        {f.size_kb} KB
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        )}

        {/* Ingest success banner */}
        {ingestData && (
          <div
            className="rounded-lg px-[var(--sp-sm)] py-[var(--sp-xs)] border-l-2"
            style={{
              background: "rgba(16,124,16,0.06)",
              borderLeftColor: "#107c10",
            }}
          >
            <span style={{ fontSize: 11, fontWeight: 700, color: "#107c10" }}>
              {ingestData.processed} file
              {ingestData.processed !== 1 ? "s" : ""} analyzed
              {ingestData.errors > 0 ? `, ${ingestData.errors} failed` : ""} —
              graphs updated
            </span>
          </div>
        )}

        {/* MCP hint */}
        <p
          style={{
            fontSize: 9,
            color: "var(--color-on-surface-variant)",
            lineHeight: 1.4,
            marginTop: 2,
          }}
        >
          Also available via MCP:{" "}
          <span style={{ fontFamily: "monospace" }}>scan_folder</span> ·{" "}
          <span style={{ fontFamily: "monospace" }}>ingest_folder</span> ·{" "}
          <span style={{ fontFamily: "monospace" }}>analyze_text</span>
        </p>
      </div>
    </section>
  );
}
