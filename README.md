# OnLooker — AI Presentation Intelligence

OnLooker is a multi-agent AI assistant that gives real-time feedback on presentations, documents, and spoken delivery. Configure your target audience in **Project Settings** and get instant coaching, simulated audience reactions, cultural fit warnings, and speech metrics — tailored to the room you're about to walk into.

**Modes**
- **Chat Box** — upload a `.pptx`, `.docx`, or `.pdf`, or type your content directly, and get AI feedback
- **Alive** — share your screen and speak; the AI coaches you live as you present

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11+ | Backend runtime |
| Node.js | 20+ | Frontend runtime |
| npm | 9+ | Bundled with Node.js |
| Groq API key | — | Free at [console.groq.com](https://console.groq.com) — powers all LLM agents |

> **No Docker or PostgreSQL needed for local development.** The backend defaults to SQLite and runs ChromaDB in-process.

---

## Quick Start

### 1. Clone and configure environment variables

```bash
git clone <repo-url>
cd AGENTS-LEAGUE-HACKATHON-2026

# Copy the safe template and add your secrets
cp .env.example .env
```

Open `.env` and set your Groq API key (the only required secret for local dev):

```env
DATABASE_URL=sqlite+aiosqlite:///./onlooker.db
GROQ_API_KEY=your_groq_api_key_here
MOCK_MODE=false
ENVIRONMENT=development
```

---

### 2. Set up the Python backend

```bash
# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install all Python dependencies
pip install -r requirements.txt
```

Start the FastAPI server (from the repo root, with the venv active):

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The backend starts at **http://localhost:8000**  
Interactive API docs: **http://localhost:8000/docs**

On first start the backend automatically:
- Creates `onlooker.db` (SQLite database)
- Seeds ChromaDB with cultural norms

---

### 3. Set up and run the frontend

```bash
cd ui-onlooker

# Install Node dependencies
npm install

# Create the frontend env file
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
echo NEXT_PUBLIC_WS_URL=ws://localhost:8000 >> .env.local

# Start the dev server
npm run dev
```

The UI starts at **http://localhost:3000**

---

### At a glance

| Service | URL | What it does |
|---|---|---|
| Frontend (Next.js) | http://localhost:3000 | OnLooker UI |
| Backend (FastAPI) | http://localhost:8000 | REST API + WebSocket |
| API Docs (Swagger) | http://localhost:8000/docs | Interactive endpoint explorer |

---

## API Endpoints

### Session management

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/session/start?persona_type=&region=&focus_area=` | Create a new session |
| `GET` | `/session/{id}` | Fetch session metadata |
| `POST` | `/session/{id}/complete` | Mark session complete |
| `GET` | `/session/{id}/analytics` | Aggregated KPI metrics |
| `POST` | `/session/{id}/report` | Generate PPTX report + email draft |
| `GET` | `/session/{id}/report/download` | Download the PPTX |

### AI Analysis (new)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze/chunk` | Analyze a text chunk — returns speech metrics, audience reaction, cultural flags, and coaching tip |
| `POST` | `/document/upload` | Upload `.pptx` / `.docx` / `.pdf` — extracts text and optionally runs AI analysis |

#### `POST /analyze/chunk` — request body

```json
{
  "text": "Your presentation content here...",
  "session_id": "chat",
  "persona_type": "executive",
  "region": "us",
  "focus_area": "business",
  "environment": "professional",
  "complexity": "medium"
}
```

#### `POST /document/upload` — form fields

| Field | Type | Default | Description |
|---|---|---|---|
| `file` | file | required | `.pptx`, `.docx`, or `.pdf` |
| `session_id` | string | `"chat"` | Session to associate with |
| `persona_type` | string | `"executive"` | `investor` / `executive` / `recruiter` / `customer` |
| `region` | string | `"us"` | `us` / `uk` / `de` / `jp` |
| `focus_area` | string | `"business"` | `business` / `technology` / `science` / `healthcare` / `research` |
| `environment` | string | `"professional"` | `professional` / `casual` |
| `complexity` | string | `"medium"` | `low` / `medium` / `high` |
| `analyze` | bool | `false` | If `true`, also runs the AI agent pipeline |

### Real-time streaming

| Protocol | Endpoint | Description |
|---|---|---|
| `WebSocket` | `/ws/stream` | Live transcript streaming for Alive mode |

Send `{"type":"init","persona":"executive","region":"us","focus_area":"business"}` first, then `{"type":"transcript_chunk","text":"..."}` for each chunk.

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | DB connectivity and version check |

---

## Project Settings → AI context

The **Project Settings** panel on the right side of the UI feeds context to every AI agent:

| Field | Effect on AI |
|---|---|
| **Type of audience** | Maps to an AI persona (Business → executive, Academic → executive, Student → customer, Casual → customer) |
| **Environment** | Tells the coaching agent whether to adapt tips for casual vs. professional delivery |
| **Complexity** | Adjusts how the audience persona reacts (low = expects simple language, high = expects technical depth) |
| **Area** | Sets the domain focus (Technology, Sciences, Healthcare, Research, Organization) |
| **Location** | Maps to a regional cultural profile (UK, Japan, Germany, US) that informs cultural flag checks |

Click **Update** to save settings and create a new backend session before sending content.

---

## Folder structure

```
AGENTS-LEAGUE-HACKATHON-2026/
│
├── .env                              ← secrets (never commit)
├── .env.example                      ← safe template with placeholders
├── requirements.txt                  ← Python dependencies
├── onlooker.db                       ← SQLite dev database (auto-created)
│
├── backend/                          ← FastAPI application
│   ├── main.py                       ← app entry point, router registration
│   ├── database.py                   ← async engine setup
│   │
│   ├── agents/                       ← AI agent implementations
│   │   ├── orchestrator.py           ← fans out to all agents in parallel
│   │   ├── speech.py                 ← pace / filler words / clarity (no LLM)
│   │   ├── audience.py               ← Llama persona reactions
│   │   ├── coaching.py               ← Llama live coaching tips
│   │   ├── cultural.py               ← ChromaDB RAG + Llama cultural flags
│   │   └── vision.py                 ← Llama 4 Scout screen-frame analysis
│   │
│   ├── routes/                       ← API route handlers
│   │   ├── health.py                 ← GET /health
│   │   ├── session.py                ← session CRUD + report generation
│   │   ├── stream.py                 ← WebSocket /ws/stream (Alive mode)
│   │   ├── analyze.py                ← POST /analyze/chunk (Chat Box)
│   │   └── document.py               ← POST /document/upload
│   │
│   ├── services/                     ← shared service layer
│   │   ├── chroma_service.py         ← ChromaDB seed + cosine query
│   │   ├── document_service.py       ← PPTX / DOCX / PDF text extraction
│   │   ├── ingestion_service.py      ← event + analytics persistence
│   │   ├── pptx_generator.py         ← branded PPTX report builder
│   │   ├── email_service.py          ← follow-up email draft (Llama)
│   │   └── blob_service.py           ← Azure Blob Storage (optional)
│   │
│   └── models/
│       └── database.py               ← SQLAlchemy async ORM models
│
├── ui-onlooker/                      ← Next.js frontend
│   ├── app/
│   │   ├── page.tsx                  ← root page: Dashboard / Analysis views
│   │   ├── layout.tsx                ← global fonts + providers
│   │   └── globals.css               ← design tokens + Tailwind base
│   │
│   ├── components/
│   │   ├── AliveModeView.tsx         ← screen share, REC timer, video AI feed
│   │   ├── ChatBoxMode.tsx           ← document upload + AI chat interface
│   │   ├── DashboardView.tsx         ← analytics / engagement visualizer
│   │   ├── ProjectSettings.tsx       ← audience context form → POST /session/start
│   │   ├── AgentStatusPanel.tsx      ← live agent status indicators
│   │   ├── AudienceReactionFeed.tsx  ← scrolling audience reactions
│   │   ├── CoachingFeed.tsx          ← live coaching tip stream
│   │   ├── CulturalFlagBanner.tsx    ← cultural mismatch warnings
│   │   ├── ScoreDashboard.tsx        ← KPI score cards
│   │   ├── OutlookEmailCard.tsx      ← M365 email draft output
│   │   ├── SessionSetup.tsx          ← session configuration wizard
│   │   ├── TeamsPanel.tsx            ← Teams-styled Q&A panel
│   │   └── ui/                       ← shadcn/ui primitives
│   │       ├── badge.tsx
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── progress.tsx
│   │       └── select.tsx
│   │
│   ├── lib/
│   │   ├── store.ts                  ← Zustand store (session, events, metrics)
│   │   ├── useWebSocket.ts           ← singleton WS hook (connect / sendFrame)
│   │   └── utils.ts                  ← cn() and shared helpers
│   │
│   └── public/
│       └── copilot-manifest.json     ← M365 Copilot plugin stub
│
├── dtos/                             ← shared Pydantic DTOs
│   ├── analytics.py
│   ├── audience.py
│   ├── reports.py
│   ├── data_ingestors.py
│   └── data_processors.py
│
├── data_processor/                   ← Data Commons fetch + profile builder
│   ├── fetch_data_commons.py
│   └── build_profiles.py
│
├── data_ingestor/                    ← one-time DB seed script
│   └── seed_database.py
│
└── containers_env/                   ← Docker Compose (optional for prod)
    ├── embeds-db/                    ← ChromaDB container config
    └── postgresql-db/                ← PostgreSQL container config
```

---

## Optional: PostgreSQL + Docker (production)

For a production-grade setup, swap SQLite for PostgreSQL and run services in containers:

```bash
cd containers_env
docker compose up -d
```

Update `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@localhost:5432/onlooker
```

Seed audience profiles (run once after database is ready):

```bash
python -m data_ingestor.seed_database
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot find module '@deemlol/next-icons'` | `transpilePackages` is set in `next.config.ts` — restart `npm run dev` |
| `ModuleNotFoundError` on Python | Activate the virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` |
| `GROQ_API_KEY` errors | Make sure `.env` exists in the repo root with a valid key from [console.groq.com](https://console.groq.com) |
| Backend returns 501 on `.docx` or `.pdf` upload | Run `pip install python-docx pypdf` (should be covered by `requirements.txt`) |
| Port 3000 already in use | `npm run dev -- -p 3001` or kill the other process |
| Port 8000 already in use | `uvicorn backend.main:app --reload --port 8001` and update `.env.local` accordingly |
| ChromaDB errors on first run | Delete the `chroma_data/` folder and restart the backend to re-seed |
| Frontend shows blank page | Check the browser console for `NEXT_PUBLIC_API_URL` errors; confirm the backend is running on port 8000 |
