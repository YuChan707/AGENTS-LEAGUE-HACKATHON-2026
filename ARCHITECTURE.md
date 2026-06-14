# Feedback Agent - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        UI Layer (Next.js)                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                     Main Page                              │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │          ProjectSettings Component                  │ │ │
│  │  │  [Audience] [Environment] [Complexity]              │ │ │
│  │  │  [Area] [Location] [Feedback Perspective] ← NEW     │ │ │
│  │  │                                                      │ │ │
│  │  │  Dropdown: academic_us | academic_europe |          │ │ │
│  │  │            business_uk | business_asia | startup |  │ │ │
│  │  │            community                                 │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                            ↓                                │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │            Chat/Live Mode                           │ │ │
│  │  │  ┌─ Speech Input ──────────────────────────────┐    │ │ │
│  │  │  │ WebSocket: init message + feedback_setting │    │ │ │
│  │  │  └─────────────────────────────────────────────┘    │ │ │
│  │  │                            ↓                          │ │ │
│  │  │  ┌──────────────────────────────────────────────┐    │ │ │
│  │  │  │   Real-time Event Streams                   │    │ │ │
│  │  │  │   ├─ Speech Analysis                        │    │ │ │
│  │  │  │   ├─ Audience Simulation                    │    │ │ │
│  │  │  │   ├─ Feedback (NEW)                         │    │ │ │
│  │  │  │   ├─ Cultural Check                         │    │ │ │
│  │  │  │   └─ Coaching Tips                          │    │ │ │
│  │  │  └──────────────────────────────────────────────┘    │ │ │
│  │  │                            ↓                          │ │ │
│  │  │  Zustand Store                                       │ │ │
│  │  │  ├─ sessionConfig: { feedbackSetting }              │ │ │
│  │  │  ├─ feedbacks: FeedbackPayload[]                    │ │ │
│  │  │  └─ addEvent(agent, payload)                        │ │ │
│  │  │                            ↓                          │ │ │
│  │  │  ┌──────────────────────────────────────────────┐    │ │ │
│  │  │  │ Display Components                          │    │ │ │
│  │  │  │ ├─ ScoreDashboard (speech)                  │    │ │ │
│  │  │  │ ├─ AudienceReactionFeed                     │    │ │ │
│  │  │  │ ├─ FeedbackFeed (NEW)  ← Shows feedback    │    │ │ │
│  │  │  │ ├─ CulturalFlagBanner                       │    │ │ │
│  │  │  │ └─ CoachingFeed                             │    │ │ │
│  │  │  └──────────────────────────────────────────────┘    │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↕ WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI/Python)                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  /ws/stream                                                │ │
│  │  WebSocket Handler                                         │ │
│  │  ├─ Accept connection                                      │ │
│  │  ├─ Parse init: { feedback_setting }                      │ │
│  │  └─ Send events to orchestrator                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Orchestrator (agents/orchestrator.py)                     │ │
│  │  SessionContext:                                            │ │
│  │  ├─ persona, region, focus_area                           │ │
│  │  ├─ feedback_setting ← NEW                                │ │
│  │  └─ environment, complexity                                │ │
│  │                                                             │ │
│  │  process(text) → parallel tasks:                           │ │
│  │  ├─ Speech Analysis (Python)                              │ │
│  │  ├─ Audience Agent (Groq API)                             │ │
│  │  ├─ Feedback Agent (Groq API) ← NEW                       │ │
│  │  ├─ Cultural Agent (Groq API)                             │ │
│  │  └─ Coaching Agent (Groq API)                             │ │
│  │                                                             │ │
│  │  yield events                                               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Feedback Agent (agents/feedback.py) ← NEW                │ │
│  │                                                             │ │
│  │  FEEDBACK_SETTINGS:                                        │ │
│  │  ├─ academic_us                                            │ │
│  │  ├─ academic_europe                                        │ │
│  │  ├─ business_uk                                            │ │
│  │  ├─ business_asia                                          │ │
│  │  ├─ startup                                                │ │
│  │  └─ community                                              │ │
│  │                                                             │ │
│  │  simulate_feedback(text, setting, complexity, env)         │ │
│  │  ├─ Select settings from FEEDBACK_SETTINGS                │ │
│  │  ├─ Build prompt with:                                    │ │
│  │  │  ├─ group, location, culture                           │ │
│  │  │  ├─ communication style                                │ │
│  │  │  ├─ values & concerns                                  │ │
│  │  │  └─ content to evaluate                                │ │
│  │  ├─ Call Groq API (llama-3.1-8b-instant)                 │ │
│  │  └─ Return JSON feedback                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Feedback API Routes (routes/feedback.py) ← NEW           │ │
│  │  ├─ GET  /feedback/settings                               │ │
│  │  ├─ POST /feedback/generate                               │ │
│  │  └─ GET  /feedback/available-perspectives                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  External Services                                         │ │
│  │  ├─ Groq API (LLM generation)                             │ │
│  │  ├─ ChromaDB (cultural norms)                             │ │
│  │  └─ PostgreSQL (session storage)                          │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow - Feedback Generation

```
User Selects Feedback Perspective
        ↓
Settings stored in Zustand store
        ↓
WebSocket connection sends init with feedback_setting
        ↓
Backend SessionContext receives feedback_setting
        ↓
User streams speech chunk
        ↓
Orchestrator.process(text) called
        ↓
5 Agents run in parallel:
  ├─ Speech Analysis
  ├─ Audience Simulation → Groq API
  ├─ Feedback Generation → Groq API ← gets feedback_setting
  ├─ Cultural Check → Groq API
  └─ Coaching → Groq API
        ↓
simulate_feedback() executes:
  ├─ Looks up FEEDBACK_SETTINGS[feedback_setting]
  ├─ Gets group, location, culture, communication_style, values, concerns
  ├─ Builds prompt with all context
  ├─ Calls Groq API
  └─ Parses JSON response
        ↓
FeedbackPayload returned:
  {
    feedback_type, relevance_score, key_concern,
    critical_question, cultural_note, recommendation,
    alignment_with_values, setting, group, location, culture
  }
        ↓
WebSocket streams to frontend
        ↓
Frontend store.addEvent("feedback", payload)
        ↓
FeedbackFeed component renders in real-time
```

## Feedback Perspectives - Decision Tree

```
                    Feedback Perspective?
                            ↓
            ┌───────────────────────────────────┐
            ↓                   ↓                ↓
         Academic        Business            Community
            ↓                   ↓                ↓
     ┌─────────────┐    ┌──────────────┐    ┌────────┐
     ↓             ↓    ↓              ↓    ↓        ↓
    US        Europe   UK          Asia  Startup  Diverse
                      
Academic_US:          Business_UK:           Business_Asia:
- Evidence-based      - Professional         - Relationship-focused
- Rigorous            - Diplomatic           - Harmony-focused
- Peer review focus   - ROI-focused          - Stakeholder alignment
- Methodology         - Time-conscious       - Collective benefit
- Statistical rigor   - Bottom line          - Long-term viability

Academic_Europe:      Startup:               Community:
- Philosophical       - Fast-paced           - Practical
- Critical analysis   - Iterative            - Accessible
- Contextual          - Disruptive           - Real-world impact
- Theoretical         - Growth-focused       - Inclusive
- Deep exploration    - Market fit           - Cultural sensitivity
```

## Component Interaction Diagram

```
ProjectSettings
    ├─ State: [feedbackSetting, audience, env, complexity]
    └─ onChange → setFeedbackSetting
            ↓
        Zustand Store
            ├─ sessionConfig.feedbackSetting
            └─ feedbacks[]
            ↓
        useWebSocket Hook
            ├─ WebSocket init message includes feedbackSetting
            ├─ Sends: {type: "init", feedback_setting: "academic_us"}
            └─ Receives events and calls store.addEvent()
            ↓
        Backend /ws/stream
            ├─ Receives init with feedback_setting
            ├─ Passes to orchestrator.configure()
            └─ Calls orchestrator.process() on each chunk
            ↓
        Orchestrator
            ├─ Runs feedback agent with context.feedback_setting
            ├─ Returns FeedbackPayload
            └─ Yields feedback event
            ↓
        WebSocket sends feedback event back to frontend
            ↓
        useWebSocket receives: {agent: "feedback", payload: {...}}
            ├─ Calls store.addEvent("feedback", payload)
            ├─ Stores in feedbacks[]
            └─ Triggers re-render
            ↓
        FeedbackFeed Component
            ├─ Subscribes to store.feedbacks
            ├─ Maps each feedback to FeedbackItem
            └─ Displays with visual styling
```

## Parallel Execution Timeline

```
Time →
0ms:  Speech chunk received
      ├─ Speech Analysis starts (Python, fast)
      ├─ Audience Agent starts (Groq API) ┐
      ├─ Feedback Agent starts (Groq API) │ Parallel
      ├─ Cultural Agent starts (Groq API) │ Execution
      └─ Coaching starts (Groq API)       ┘

1000-2000ms:
      Async gathering completes:
      ├─ Speech analysis: ~10ms
      ├─ Audience: ~1500ms
      ├─ Feedback: ~1500ms  ← Same speed
      ├─ Cultural: ~1000ms
      └─ Coaching: ~800ms

2000ms: All events yielded to WebSocket
        │
        ├─ speech_event
        ├─ audience_event
        ├─ feedback_event  ← Real-time
        ├─ cultural_event
        └─ coaching_event

2100ms: All events received by frontend
        ├─ Store updated with all payloads
        ├─ Components re-render
        └─ User sees all feedback in UI

Total latency: ~2 seconds (independent of feedback addition)
```

## State Management Flow

```
Frontend Store (Zustand)

SessionConfig {
  personaType: string
  region: string
  focusArea: string
  environment: string
  complexity: string
  feedbackSetting: string ← NEW
}

Events[] {
  agent: "speech" | "audience" | "feedback" | ... ← NEW TYPE
  payload: SpeechPayload | AudiencePayload | FeedbackPayload | ...
}

Feedbacks[] {
  feedback_type: string
  relevance_score: number
  key_concern: string
  critical_question: string
  cultural_note: string | null
  recommendation: string
  alignment_with_values: string
  setting: string
  group: string
  location: string
  culture: string
}
```

## API Endpoint Architecture

```
/feedback (NEW)
├─ GET /feedback/settings
│   └─ Returns: { "academic_us": {...}, "business_uk": {...}, ... }
│
├─ GET /feedback/available-perspectives
│   └─ Returns: { "academic": {...}, "business": {...}, "community": {...} }
│
└─ POST /feedback/generate
    ├─ Request: { text, feedback_setting, complexity, environment }
    └─ Response: { agent: "feedback", payload: FeedbackPayload }
```

## Integration Points Summary

| Component | Integration | Purpose |
|-----------|-------------|---------|
| **ProjectSettings** | Dropdown selector | Configure perspective |
| **useWebSocket** | Pass feedbackSetting | Send to backend |
| **Orchestrator** | Include in SessionContext | Use during processing |
| **Feedback Agent** | Run in parallel | Generate responses |
| **Stream WebSocket** | Accept parameter | Receive setting |
| **Store** | Add feedbacks array | Track responses |
| **FeedbackFeed** | Subscribe & display | Show user feedback |

---

**The Feedback Agent seamlessly integrates into the existing architecture without disrupting other components!**
