#!/usr/bin/env python3
"""
OnLooker MCP Server — stdio transport, JSON-RPC 2.0.

Tools exposed to Claude Code / any MCP client:
  scan_folder    List PPTX/DOCX/PDF files in a local folder.
  ingest_folder  Run AI analysis on every file in a folder.
  analyze_text   Analyze arbitrary text through the AI pipeline.

Start the FastAPI backend first:
  uvicorn backend.main:app --reload --port 8000

The .claude/mcp.json in this directory is already wired to launch this server.
"""
import asyncio
import json
import sys

import httpx

BACKEND = "http://localhost:8000"

# ── Tool manifests ────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "scan_folder",
        "description": (
            "List all PPTX, DOCX, and PDF files in a local folder without running AI analysis. "
            "Use this to preview what will be ingested before calling ingest_folder."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "folder_path": {
                    "type": "string",
                    "description": "Absolute path to a local folder (e.g. C:\\Users\\Alice\\Slides or ~/presentations)",
                }
            },
            "required": ["folder_path"],
        },
    },
    {
        "name": "ingest_folder",
        "description": (
            "Process every PPTX/DOCX/PDF document in a local folder through the OnLooker AI pipeline. "
            "Returns per-file analysis: audience fit scores, language tone, key coaching tip, and engagement graph data."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "folder_path": {"type": "string", "description": "Absolute path to the folder to ingest"},
                "persona_type": {"type": "string", "description": "executive | investor | customer | academic", "default": "executive"},
                "region": {"type": "string", "description": "us | uk | jp | de | fr | sg", "default": "us"},
                "focus_area": {"type": "string", "description": "business | technology | science | healthcare", "default": "business"},
                "environment": {"type": "string", "description": "professional | casual", "default": "professional"},
                "complexity": {"type": "string", "description": "easy | medium | complex", "default": "medium"},
            },
            "required": ["folder_path"],
        },
    },
    {
        "name": "analyze_text",
        "description": (
            "Analyze a passage of presentation text through the OnLooker AI agent pipeline. "
            "Returns speech metrics, audience reactions, cultural flags, and a coaching tip."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Presentation text or transcript chunk to analyze"},
                "persona_type": {"type": "string", "default": "executive"},
                "region": {"type": "string", "default": "us"},
                "focus_area": {"type": "string", "default": "business"},
            },
            "required": ["text"],
        },
    },
]

# ── Backend call helper ───────────────────────────────────────────────────────

async def _post(path: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{BACKEND}{path}", json=body)
        resp.raise_for_status()
        return resp.json()

# ── Per-tool formatters ───────────────────────────────────────────────────────

def _fmt_scan(data: dict) -> str:
    if data.get("error"):
        return f"Error: {data['error']}"
    lines = [
        f"Folder : {data['folder_name']}",
        f"Path   : {data['folder_path']}",
        f"Files  : {data['file_count']}",
        "",
    ]
    for f in data.get("files", []):
        lines.append(f"  [{f['ext'].upper():4s}] {f['name']}  ({f['size_kb']} KB)")
    return "\n".join(lines)


def _fmt_file_result(r: dict) -> list[str]:
    if r["status"] != "success":
        return [f"[{r['filename']}] ERROR: {r.get('error', 'unknown')}", ""]
    a = r.get("analysis", {})
    s = a.get("success_scores", {})
    return [
        f"[{r['filename']}]",
        f"  Type   : {a.get('doc_type', '?')}  |  Tone: {a.get('language_tone', '?')}",
        f"  Scores : Audience {s.get('audience', '?')}%  Env {s.get('environment', '?')}%  Complexity {s.get('complexity', '?')}%",
        f"  Words  : {r['word_count']}",
        f"  Tip    : {a.get('short_feedback', '')}",
        "",
    ]


def _fmt_ingest(data: dict) -> str:
    if data.get("error"):
        return f"Error: {data['error']}"
    lines = [
        f"Folder    : {data['folder_name']}",
        f"Processed : {data['processed']}  |  Errors: {data['errors']}",
        "",
    ]
    for r in data.get("results", []):
        lines.extend(_fmt_file_result(r))
    return "\n".join(lines)


def _fmt_event(ev: dict) -> str:
    agent = ev.get("agent", "")
    p = ev.get("payload", {})
    if agent == "speech":
        return (
            f"Speech : {p.get('pace_wpm')} WPM | "
            f"Fillers: {p.get('filler_count')} | "
            f"Clarity: {round(p.get('clarity_score', 0) * 100)}%"
        )
    if agent == "coaching":
        return f"Coaching : {p.get('tip')}"
    if agent == "cultural" and p.get("flag"):
        return f"Cultural : {p.get('issue')} → {p.get('fix')}"
    if agent == "audience":
        return f"Audience ({p.get('speaker')}) : {p.get('reaction_type')} — \"{p.get('internal_thought')}\""
    if agent == "feedback":
        return f"Feedback [{p.get('group')}] : {p.get('key_concern')}"
    return ""


def _fmt_analyze(data: dict) -> str:
    lines = [s for ev in data.get("events", []) if (s := _fmt_event(ev))]
    return "\n".join(lines) if lines else json.dumps(data, indent=2)

# ── Tool dispatcher ───────────────────────────────────────────────────────────

async def handle_tool(name: str, args: dict) -> str:
    try:
        if name == "scan_folder":
            return _fmt_scan(await _post("/folder/scan", {"folder_path": args["folder_path"]}))
        if name == "ingest_folder":
            return _fmt_ingest(await _post("/folder/ingest", args))
        if name == "analyze_text":
            body = {
                "text": args["text"],
                "session_id": "mcp",
                "persona_type": args.get("persona_type", "executive"),
                "region": args.get("region", "us"),
                "focus_area": args.get("focus_area", "business"),
            }
            return _fmt_analyze(await _post("/analyze/chunk", body))
        return json.dumps({"error": f"Unknown tool: {name}"})
    except httpx.ConnectError:
        return (
            "Error: OnLooker backend is not running.\n"
            "Start it with:  uvicorn backend.main:app --reload --port 8000\n"
            "(run from the AGENTS-LEAGUE-HACKATHON-2026 directory)"
        )
    except Exception as exc:
        return f"Error: {exc}"

# ── Wire protocol helpers ─────────────────────────────────────────────────────

def _write(obj: dict) -> None:
    body = json.dumps(obj).encode()
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
    sys.stdout.buffer.flush()


def _parse_length(header_bytes: bytes) -> int | None:
    for line in header_bytes.split(b"\r\n"):
        if line.lower().startswith(b"content-length:"):
            return int(line.split(b":", 1)[1].strip())
    return None


async def _dispatch(req: dict) -> None:
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "initialize":
        _write({"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "onlooker-mcp", "version": "1.0.0"},
        }})
    elif method == "notifications/initialized":
        return  # no response for notifications
    elif method == "tools/list":
        _write({"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}})
    elif method == "tools/call":
        text = await handle_tool(params.get("name", ""), params.get("arguments", {}))
        _write({"jsonrpc": "2.0", "id": rid,
                "result": {"content": [{"type": "text", "text": text}]}})
    elif rid is not None:
        _write({"jsonrpc": "2.0", "id": rid,
                "error": {"code": -32601, "message": f"Method not found: {method}"}})

# ── Main loop ─────────────────────────────────────────────────────────────────

async def main() -> None:
    loop = asyncio.get_event_loop()
    buf = b""
    while True:
        chunk = await loop.run_in_executor(None, sys.stdin.buffer.read1, 8192)
        if not chunk:
            break
        buf += chunk
        while b"\r\n\r\n" in buf:
            header_part, rest = buf.split(b"\r\n\r\n", 1)
            length = _parse_length(header_part)
            if length is None or len(rest) < length:
                break
            body_bytes, buf = rest[:length], rest[length:]
            try:
                await _dispatch(json.loads(body_bytes))
            except json.JSONDecodeError:
                pass


if __name__ == "__main__":
    asyncio.run(main())
