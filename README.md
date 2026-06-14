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

# Quick Start Guide - Feedback Agent

## 🚀 Getting Started in 5 Minutes

### Step 1: Verify Installation
Ensure all dependencies are installed:
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd ui-onlooker
npm install
```

### Step 2: Start the Backend
```bash
cd backend
python -m uvicorn main:app --reload
```
Expected output:
```
Starting Onlooker API...
Database + ChromaDB ready
Uvicorn running on http://127.0.0.1:8000
```

### Step 3: Start the Frontend
```bash
cd ui-onlooker
npm run dev
```
Expected output:
```
▲ Next.js ...
- Local: http://localhost:3000
```

### Step 4: Configure Feedback Settings
1. Open http://localhost:3000
2. Scroll to "Project Settings"
3. Select **Feedback Perspective** dropdown
4. Choose one of 6 perspectives:
   - Academic (US or Europe)
   - Business (UK, Asia, or Startup)
   - Community

### Step 5: Start a Session
1. Fill in other settings (Type of Audience, Environment, Complexity)
2. Click **"Update"**
3. Start streaming content (chat or live mode)
4. Watch feedback appear in real-time!

## 📊 What You'll See

When you stream content, feedback will show:

```
┌─────────────────────────────────────┐
│ Location — Group                    │
│ Relevance: 8/10                     │
│                                     │
│ Main Concern: [specific concern]    │
│ Cultural Note: [if applicable]      │
│ They would ask: "Question here?"    │
│ Recommendation: [actionable advice] │
│ Values Alignment: [assessment]      │
└─────────────────────────────────────┘
```

## 🎯 6 Feedback Perspectives Explained

| Perspective | Location | Culture | Best For |
|-------------|----------|---------|----------|
| **academic_us** | United States | Western | Research, evidence-based content |
| **academic_europe** | Europe | Western | Theoretical, philosophical content |
| **business_uk** | United Kingdom | Western | Professional, diplomatic content |
| **business_asia** | Asia | Eastern | Relationship-focused, consensus-building |
| **startup** | Global | Innovation | Fast-paced, disruptive ideas |
| **community** | Diverse | Multicultural | Practical, accessible content |

## 🧪 Test the API Directly

### Get Available Perspectives
```bash
curl http://localhost:8000/feedback/available-perspectives
```

### Generate Feedback
```bash
curl -X POST http://localhost:8000/feedback/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "We have disrupted the market with AI-powered solutions",
    "feedback_setting": "startup",
    "complexity": "medium",
    "environment": "professional"
  }'
```

### Get All Settings
```bash
curl http://localhost:8000/feedback/settings
```

## 🔧 Customize Perspectives

### Add a New Perspective

Edit `backend/agents/feedback.py`:

```python
FEEDBACK_SETTINGS = {
    "your_perspective": {
        "group": "business",
        "location": "Your City",
        "culture": "Your Culture",
        "communication_style": "descriptive style",
        "values": "core values",
        "concerns": ["concern1", "concern2", "concern3"]
    }
}
```

Then restart the backend and the new option appears in the dropdown!

## 📈 Performance Expectations

| Metric | Value |
|--------|-------|
| Feedback Generation Time | 1-2 seconds |
| Parallel Execution | Yes (no latency added) |
| Response Size | ~200-300 tokens |
| Real-time Display | <1 second |

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| No feedback appearing | Check backend logs, verify GROQ_API_KEY set |
| Slow feedback | Network latency or Groq API load - wait a moment |
| Wrong perspective | Verify feedbackSetting in dropdown, reset session |
| Frontend can't connect | Check API_BASE in .env or ProjectSettings.tsx |

## 📝 Key Files to Know

```
backend/
├── agents/
│   ├── feedback.py          ← New feedback generation logic
│   └── orchestrator.py      ← Updated to run feedback in parallel
├── routes/
│   ├── feedback.py          ← New API endpoints
│   └── stream.py            ← Updated for feedback_setting
└── main.py                  ← Updated router registration

ui-onlooker/
├── components/
│   ├── FeedbackFeed.tsx      ← New UI component
│   └── ProjectSettings.tsx   ← Updated with perspective selector
├── lib/
│   ├── store.ts             ← Updated state management
│   └── useWebSocket.ts      ← Updated WebSocket
```

## 🎓 Learn More

For detailed documentation:
- **FEEDBACK_AGENT_GUIDE.md** - Complete technical guide
- **IMPLEMENTATION_SUMMARY.md** - What was changed and why

## ✨ Key Features

✅ **Real-time Feedback** - See feedback as you speak
✅ **6 Perspectives** - Academic, Business, Community views
✅ **Cultural Awareness** - Get cultural notes and alignment scores
✅ **Actionable Advice** - Specific recommendations to improve
✅ **Parallel Processing** - No performance impact
✅ **Customizable** - Easy to add your own perspectives

## 🚀 Next Steps

1. **Integrate into Dashboard** - Add FeedbackFeed to your dashboard
2. **Export Feedback** - Generate feedback reports
3. **Compare Perspectives** - Show multiple perspectives side-by-side
4. **Track Metrics** - Monitor feedback types and scores
5. **Custom Perspectives** - Create domain-specific audiences

## 💡 Pro Tips

- Use **academic_us** for technical/research content
- Use **business_asia** for international business pitches
- Use **startup** for innovative or disruptive ideas
- Use **community** to test accessibility and inclusivity
- Adjust **complexity** to match your audience
- Switch perspectives between practice sessions

---

**Ready to get feedback from multiple perspectives?** Start streaming now! 🎤
