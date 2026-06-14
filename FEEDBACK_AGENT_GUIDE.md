# AI Feedback Agent - Implementation Guide

## Overview

The **Feedback Agent** is a new AI-powered component that simulates feedback responses from different audience perspectives. It allows presenters to get contextual, culturally-aware feedback on their content based on specific audience profiles defined by:

- **Location/Region** (e.g., United States, Europe, Asia)
- **Culture** (e.g., Western, Eastern, Multicultural)
- **Group Type** (e.g., Academic, Business, Community)
- **Ethnicity & Cultural Background**

This helps presenters understand how their message resonates with different demographic groups and cultural contexts.

## Architecture

### Backend Components

#### 1. **Feedback Agent** (`backend/agents/feedback.py`)

The core agent that generates feedback simulations using LLMs.

**Key Features:**
- 6 pre-configured feedback perspectives
- Context-aware evaluation based on audience values and concerns
- Relevance scoring (1-10)
- Cultural sensitivity analysis
- Actionable recommendations

**Available Settings:**
- `academic_us`: US academic setting, Western culture, evidence-based
- `academic_europe`: European academic, Western culture, philosophical
- `business_uk`: UK business, Western culture, professional
- `business_asia`: Asian business, Eastern culture, relationship-focused
- `startup`: Global startup environment, innovation-focused
- `community`: Community groups, Multicultural, practical focus

**API Response Structure:**
```json
{
  "agent": "feedback",
  "type": "feedback",
  "payload": {
    "feedback_type": "constructive|critical|supportive|skeptical",
    "relevance_score": 1-10,
    "key_concern": "string",
    "critical_question": "string",
    "cultural_note": "string or null",
    "recommendation": "string",
    "alignment_with_values": "string",
    "setting": "academic_us",
    "group": "academic",
    "location": "United States",
    "culture": "Western"
  }
}
```

#### 2. **Feedback Routes** (`backend/routes/feedback.py`)

RESTful API endpoints for feedback operations.

**Endpoints:**

##### `GET /feedback/settings`
Returns all available feedback settings with their configurations.

**Response:**
```json
{
  "academic_us": {
    "group": "academic",
    "location": "United States",
    "culture": "Western"
  },
  ...
}
```

##### `POST /feedback/generate`
Generate feedback for specific content.

**Request:**
```json
{
  "text": "Your presentation text here",
  "feedback_setting": "academic_us",
  "complexity": "medium",
  "environment": "professional"
}
```

**Response:**
```json
{
  "agent": "feedback",
  "type": "feedback",
  "payload": { /* feedback object */ }
}
```

##### `GET /feedback/available-perspectives`
Get all feedback perspectives organized by category.

**Response:**
```json
{
  "academic": {
    "academic_us": { "label": "United States - Western", ... },
    ...
  },
  "business": { ... },
  "community": { ... }
}
```

#### 3. **Orchestrator Integration** (`backend/agents/orchestrator.py`)

The feedback agent runs **in parallel** with audience and cultural agents:

```python
feedback_task = asyncio.create_task(
    simulate_feedback(text, ctx.feedback_setting, ctx.complexity, ctx.environment)
)
```

**Session Context Updates:**
- Added `feedback_setting: str = "academic_us"` parameter
- Feedback agent runs on every speech analysis

#### 4. **WebSocket Stream** (`backend/routes/stream.py`)

Updated to accept `feedback_setting` in the init message:

```json
{
  "type": "init",
  "persona": "investor",
  "region": "us",
  "focus_area": "finance",
  "feedback_setting": "academic_us"
}
```

### Frontend Components

#### 1. **Store Updates** (`ui-onlooker/lib/store.ts`)

**New Types:**
```typescript
export interface FeedbackPayload {
  feedback_type: string;
  relevance_score: number;
  key_concern: string;
  critical_question: string;
  cultural_note: string | null;
  recommendation: string;
  alignment_with_values: string;
  setting: string;
  group: string;
  location: string;
  culture: string;
}
```

**Store Updates:**
- Added `feedbacks: FeedbackPayload[]` to track all feedback
- Added `feedbackSetting` to `SessionConfig`
- Updated event handling to collect feedback payloads

#### 2. **ProjectSettings Component** (`ui-onlooker/components/ProjectSettings.tsx`)

**New Field:** Feedback Perspective selector

```tsx
<select value={feedbackSetting} onChange={(e) => setFeedbackSetting(e.target.value)}>
  <optgroup label="Academic">
    <option value="academic_us">United States - Western</option>
    <option value="academic_europe">Europe - Western</option>
  </optgroup>
  <optgroup label="Business">
    <option value="business_uk">United Kingdom - Western</option>
    <option value="business_asia">Asia - Eastern</option>
    <option value="startup">Global - Innovation-focused</option>
  </optgroup>
  <optgroup label="Community">
    <option value="community">Diverse - Multicultural</option>
  </optgroup>
</select>
```

#### 3. **FeedbackFeed Component** (`ui-onlooker/components/FeedbackFeed.tsx`)

Real-time display of feedback responses.

**Features:**
- Visual feedback type indicators (constructive/critical/skeptical/supportive)
- Relevance scoring
- Cultural notes highlighting
- Critical questions display
- Action recommendations

**Usage:**
```tsx
<FeedbackFeed />
```

#### 4. **WebSocket Updates** (`ui-onlooker/lib/useWebSocket.ts`)

Passes `feedback_setting` during connection init:

```typescript
_ws!.send(
  JSON.stringify({
    type: "init",
    persona: configRef.current.personaType,
    region: configRef.current.region,
    focus_area: configRef.current.focusArea,
    feedback_setting: configRef.current.feedbackSetting || "academic_us",
  })
);
```

## Usage Flow

### For Users

1. **Configure Settings:**
   - Select "Feedback Perspective" in Project Settings
   - Choose from 6 pre-configured perspectives
   - Settings update when submitted

2. **Stream Presentation:**
   - Start recording/streaming
   - System automatically generates feedback in parallel with other agents
   - Feedback appears in FeedbackFeed component

3. **Review Feedback:**
   - See real-time feedback from selected perspective
   - Understand key concerns of that audience
   - Get actionable recommendations
   - View cultural notes and alignment scores

### For Developers

#### Extending Feedback Perspectives

Add new perspectives in `backend/agents/feedback.py`:

```python
FEEDBACK_SETTINGS = {
    "my_perspective": {
        "group": "business",
        "location": "India",
        "culture": "Eastern",
        "communication_style": "...",
        "values": "...",
        "concerns": ["concern1", "concern2", ...]
    }
}
```

#### Customizing Feedback Prompts

Modify `FEEDBACK_PROMPT` template to adjust:
- Evaluation criteria
- Response format
- Feedback types
- Scoring methodology

#### Using Feedback Directly

```python
from agents.feedback import simulate_feedback

feedback = await simulate_feedback(
    text="Your content here",
    feedback_setting="academic_us",
    complexity="medium",
    environment="professional"
)
```

## Technical Details

### Performance

- **Parallel Execution:** Runs alongside audience and cultural agents
- **Token Efficiency:** 300 token limit per response
- **Temperature:** 0.6 (balanced creative + deterministic)
- **Model:** Groq llama-3.1-8b-instant

### Customization Settings

| Setting | Values | Impact |
|---------|--------|--------|
| `feedback_setting` | 6 options | Audience perspective |
| `complexity` | low/medium/high | Content depth consideration |
| `environment` | professional/academic/community | Context adjustment |

### Error Handling

- Graceful fallback if API fails
- Returns supportive feedback with neutral score
- Continues streaming without interruption

## Integration Points

### Connect to Backend

**API Base:** `http://localhost:8000` (configurable)

**Environment Variable:**
```bash
NEXT_PUBLIC_API_URL=http://your-api-url:8000
```

### Settings Persistence

Settings stored in Zustand store:
- Persists across WebSocket reconnections
- Updated when Project Settings form submitted
- Used for all subsequent feedback requests

## Examples

### Example 1: Academic Feedback Flow

```
User Input: "Our startup achieved 300% growth through aggressive marketing"
Setting: academic_us
Response:
- Feedback Type: skeptical
- Key Concern: "Lack of peer-reviewed evidence"
- Critical Question: "What is your statistical methodology?"
- Recommendation: "Include methodology and cite published studies"
- Relevance: 7/10
```

### Example 2: Business Feedback Flow

```
User Input: "Our research shows positive sentiment in community feedback"
Setting: business_asia
Response:
- Feedback Type: constructive
- Key Concern: "Team alignment and stakeholder buy-in"
- Cultural Note: "Consider formal stakeholder alignment meeting"
- Recommendation: "Present to stakeholders for consensus-building"
- Relevance: 8/10
```

## Testing

### Manual Testing

1. Start backend: `python -m uvicorn backend.main:app --reload`
2. Start frontend: `npm run dev`
3. Select "Feedback Perspective" in settings
4. Start streaming presentation
5. Observe feedback in FeedbackFeed component

### API Testing

```bash
curl -X POST http://localhost:8000/feedback/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Sample presentation content",
    "feedback_setting": "academic_us",
    "complexity": "medium",
    "environment": "professional"
  }'
```

## Future Enhancements

- [ ] Custom feedback perspective creation UI
- [ ] Feedback history and analysis dashboard
- [ ] Multi-perspective feedback comparison
- [ ] Demographic profiling for audience feedback
- [ ] Real-time feedback aggregation metrics
- [ ] Feedback export and reporting

## Troubleshooting

### Feedback Not Appearing

1. Check WebSocket connection in DevTools
2. Verify `feedback_setting` is passed in init message
3. Check backend logs for errors
4. Ensure Groq API key is configured

### Slow Feedback Generation

- Check network latency to backend
- Verify Groq API is responding
- Consider reducing content length
- Monitor token usage

### Incorrect Perspective

- Verify `feedback_setting` value matches FEEDBACK_SETTINGS keys
- Check store contains correct feedbackSetting
- Reset session and reconfigure settings

## Deployment Checklist

- [ ] Environment variable `GROQ_API_KEY` set
- [ ] Backend routes registered in main.py
- [ ] Frontend components imported in pages
- [ ] WebSocket connection configured
- [ ] Store initialized with feedback defaults
- [ ] CSS classes available (Tailwind)
- [ ] API_BASE URL correct for environment
