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
