# Feedback Settings & Customization Guide

## Understanding Feedback Perspectives

Each perspective is configured with 5 key attributes that shape how feedback is generated:

### 1. **academic_us** - United States Academic Setting

```
Profile:
├─ Group: Academic (Universities, Research Institutes)
├─ Location: United States
├─ Culture: Western
├─ Communication Style: Formal, evidence-based, citations required
└─ Core Values: Rigor, peer review, methodology, reproducibility

Key Concerns:
├─ Methodology rigor and validity
├─ Statistical significance
├─ Reproducibility of results
└─ Source credibility and citations

Typical Feedback:
├─ Type: Often skeptical/critical
├─ Score: 7-8/10 (reasonable baseline)
├─ Focus: Evidence quality, research design
├─ Questions: "What's your statistical methodology?", "Is this peer-reviewed?"
└─ Recommendation: Add citations, strengthen methodology

Best For:
├─ Research presentations
├─ Scientific talks
├─ Academic conference pitches
└─ Data-heavy content
```

### 2. **academic_europe** - European Academic Setting

```
Profile:
├─ Group: Academic (Universities, Research Centers)
├─ Location: Europe
├─ Culture: Western
├─ Communication Style: Philosophical, critical, detailed
└─ Core Values: Depth, critique, contextualization, theory

Key Concerns:
├─ Historical context and relevance
├─ Theoretical framework alignment
├─ Societal and ethical implications
└─ Comprehensive analysis

Typical Feedback:
├─ Type: Often critical with constructive elements
├─ Score: 6-7/10 (higher bar for approval)
├─ Focus: Theory, context, implications
├─ Questions: "What's the theoretical basis?", "How does this fit historically?"
└─ Recommendation: Add theoretical framework, discuss broader implications

Best For:
├─ Philosophy/theory discussions
├─ Humanities presentations
├─ Critical analysis
└─ Policy papers
```

### 3. **business_uk** - United Kingdom Business Setting

```
Profile:
├─ Group: Business (Corporations, Investors, Partners)
├─ Location: United Kingdom
├─ Culture: Western
├─ Communication Style: Professional, diplomatic, understated humor
└─ Core Values: Efficiency, ROI, bottom line, practicality

Key Concerns:
├─ Business case and financial impact
├─ Cost-benefit analysis
├─ Implementation timeline
├─ Risk management

Typical Feedback:
├─ Type: Constructive and pragmatic
├─ Score: 7-8/10 (practical assessment)
├─ Focus: Business impact, implementation
├─ Questions: "What's the ROI?", "How quickly can we implement?"
└─ Recommendation: Add financial metrics, implementation plan

Best For:
├─ Business pitches
├─ Investment presentations
├─ Corporate strategy
├─ Product launches
```

### 4. **business_asia** - Asian Business Setting

```
Profile:
├─ Group: Business (Corporations, Partners, Stakeholders)
├─ Location: Asia
├─ Culture: Eastern
├─ Communication Style: Indirect, hierarchical respect, relationship-focused
└─ Core Values: Harmony, long-term relationships, collective benefit, trust

Key Concerns:
├─ Team harmony and alignment
├─ Stakeholder buy-in and consensus
├─ Cultural sensitivity
├─ Long-term viability and sustainability

Typical Feedback:
├─ Type: Supportive with gentle suggestions
├─ Score: 7-9/10 (values harmony)
├─ Focus: Consensus, relationships, sustainability
├─ Questions: "Will all stakeholders align?", "How does this serve everyone?"
├─ Cultural Note: "Consider formal alignment meetings"
└─ Recommendation: Emphasize collective benefits, stakeholder alignment

Best For:
├─ International business pitches
├─ Partnership proposals
├─ Long-term strategy
├─ Cross-cultural initiatives
```

### 5. **startup** - Global Startup Ecosystem

```
Profile:
├─ Group: Business (Startup Community, VCs, Founders)
├─ Location: Global
├─ Culture: Innovation-focused
├─ Communication Style: Fast-paced, iterative, direct
└─ Core Values: Speed, innovation, disruption potential, growth

Key Concerns:
├─ Market fit and validation
├─ Scalability potential
├─ Competitive advantage
├─ Growth potential and metrics

Typical Feedback:
├─ Type: Constructive with focus on scaling
├─ Score: 7-8/10 (measured optimism)
├─ Focus: Growth, innovation, market potential
├─ Questions: "What's your growth trajectory?", "How do you scale?"
└─ Recommendation: Show metrics, growth strategy, market traction

Best For:
├─ Startup pitches
├─ Venture capital presentations
├─ Product demos
├─ Growth strategy talks
```

### 6. **community** - Community & Multicultural Setting

```
Profile:
├─ Group: Community (Non-profits, Community Groups, Diverse Audiences)
├─ Location: Diverse
├─ Culture: Multicultural
├─ Communication Style: Accessible, practical, storytelling
└─ Core Values: Relevance, real-world impact, inclusivity, accessibility

Key Concerns:
├─ Practical application
├─ Community benefit
├─ Accessibility and understandability
├─ Cultural appropriateness

Typical Feedback:
├─ Type: Supportive and constructive
├─ Score: 7-8/10 (values inclusion)
├─ Focus: Practical impact, accessibility, inclusivity
├─ Questions: "How does this help my community?", "Can everyone understand this?"
└─ Recommendation: Use simpler language, emphasize practical benefits

Best For:
├─ Community presentations
├─ Non-profit pitches
├─ Social impact initiatives
├─ Accessibility-focused content
```

## Customizing and Extending Perspectives

### How to Add a New Perspective

Edit `backend/agents/feedback.py`:

```python
FEEDBACK_SETTINGS = {
    "your_new_perspective": {
        "group": "academic|business|community",
        "location": "City/Country/Region",
        "culture": "Western|Eastern|Multicultural|Innovation|etc",
        "communication_style": "descriptive style that fits audience",
        "values": "comma-separated core values",
        "concerns": [
            "concern 1",
            "concern 2", 
            "concern 3",
            "concern 4"
        ]
    }
}
```

Then:
1. Restart backend
2. New perspective appears in UI dropdown
3. Can be selected and used immediately

### Example: Add a Legal/Compliance Perspective

```python
"legal_compliance": {
    "group": "business",
    "location": "Global",
    "culture": "Regulatory-focused",
    "communication_style": "precise, detailed, risk-aware",
    "values": "compliance, liability mitigation, regulatory adherence",
    "concerns": [
        "regulatory compliance",
        "legal liability",
        "data privacy and security",
        "contractual obligations"
    ]
}
```

After restart, users can select "legal_compliance" from the dropdown!

## Settings Configuration Hierarchy

```
┌─ SessionConfig
│
├─ personaType: string
│  └─ How to map audience type to backend persona
│     ├─ "Business" → "executive"
│     ├─ "Academic" → "executive"
│     └─ "Student" → "customer"
│
├─ region: string
│  └─ Geographic region for cultural norms
│     ├─ "us", "uk", "de", "jp"
│     └─ Used by cultural agent (ChromaDB)
│
├─ focusArea: string
│  └─ Industry/topic focus
│     ├─ "finance", "technology", "science"
│     └─ Used for context-specific feedback
│
├─ environment: string
│  └─ Presentation context
│     ├─ "professional" (formal)
│     ├─ "academic" (research)
│     └─ "community" (public)
│
├─ complexity: string
│  └─ Content difficulty level
│     ├─ "low" (accessible)
│     ├─ "medium" (general audience)
│     └─ "high" (expert audience)
│
└─ feedbackSetting: string ← NEW
   └─ Which perspective to evaluate from
      ├─ "academic_us"
      ├─ "academic_europe"
      ├─ "business_uk"
      ├─ "business_asia"
      ├─ "startup"
      └─ "community"
```

## How Settings Affect Feedback

### Setting Impact Matrix

| Setting | Affects | Example |
|---------|---------|---------|
| **feedbackSetting** | Main evaluation lens | Academic: skeptical about evidence |
| **complexity** | Depth of feedback | Low: more accessible, High: technical |
| **environment** | Context awareness | Professional: formal tone, Community: accessible |
| **focusArea** | Domain-specific concerns | Finance: ROI focus, Tech: scalability |
| **region** | Cultural norms | US: direct, Asia: indirect |

### Example Scenario 1: Technical Research Talk

**Settings:**
- feedbackSetting: `academic_us`
- complexity: `high`
- environment: `academic`
- focusArea: `technology`

**Resulting Feedback:**
- Type: Skeptical/critical
- Concerns: Methodology, statistical rigor, citations
- Questions: "What's your research methodology?"
- Recommendation: Add peer review, strengthen statistical analysis

### Example Scenario 2: Startup Pitch

**Settings:**
- feedbackSetting: `startup`
- complexity: `medium`
- environment: `professional`
- focusArea: `technology`

**Resulting Feedback:**
- Type: Constructive
- Concerns: Market fit, scalability, competitive advantage
- Questions: "What's your growth trajectory?"
- Recommendation: Show metrics, clarify market positioning

### Example Scenario 3: Community Presentation

**Settings:**
- feedbackSetting: `community`
- complexity: `low`
- environment: `community`
- focusArea: `technology`

**Resulting Feedback:**
- Type: Supportive/encouraging
- Concerns: Practical application, accessibility
- Questions: "How does this help our community?"
- Recommendation: Use simpler language, show real-world benefits

## Advanced Customization

### Modifying Feedback Generation Prompt

Edit `FEEDBACK_PROMPT` in `backend/agents/feedback.py`:

```python
FEEDBACK_PROMPT = '''You are providing feedback as {group} audience...
[Customize the prompt template here]
'''
```

Changes affect:
- Evaluation criteria
- Response format and structure
- Types of concerns raised
- Recommendations offered

### Adjusting LLM Parameters

In `simulate_feedback()`:

```python
response = await client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=300,        # ← Adjust response length
    temperature=0.6,        # ← 0=deterministic, 1=creative
)
```

**Temperature adjustment:**
- `0.3`: More consistent, critical feedback
- `0.6`: Balanced (default)
- `0.9`: More creative, diverse perspectives

## Testing Different Configurations

### Systematic Testing Script

```python
import asyncio
from agents.feedback import simulate_feedback

test_content = "Our AI solution increases productivity by 300%"

test_cases = [
    ("academic_us", "high"),
    ("academic_europe", "high"),
    ("business_uk", "medium"),
    ("business_asia", "medium"),
    ("startup", "medium"),
    ("community", "low"),
]

async def test_all():
    for setting, complexity in test_cases:
        feedback = await simulate_feedback(
            text=test_content,
            feedback_setting=setting,
            complexity=complexity,
            environment="professional"
        )
        print(f"\n{setting} (complexity: {complexity})")
        print(f"Type: {feedback['payload']['feedback_type']}")
        print(f"Score: {feedback['payload']['relevance_score']}/10")
        print(f"Concern: {feedback['payload']['key_concern']}")

asyncio.run(test_all())
```

## Performance Considerations

### Token Usage by Perspective

| Perspective | Avg Tokens | Impact |
|-------------|-----------|--------|
| academic_us | 180-220 | Standard |
| academic_europe | 200-240 | More detailed |
| business_uk | 160-200 | More concise |
| business_asia | 180-220 | Context-heavy |
| startup | 170-210 | Focus on metrics |
| community | 180-220 | More explanatory |

**Optimization:** Longer perspectives use more tokens. Monitor token usage if scaling.

## Best Practices

### 1. **Match Audience Perspective**
- Use `academic_us` for research-heavy content
- Use `business_asia` for international partnerships
- Use `startup` for innovation pitches
- Use `community` for public initiatives

### 2. **Adjust Complexity**
- Lower complexity → more forgiving feedback
- Higher complexity → stricter evaluation
- Match to your actual audience

### 3. **Test Multiple Perspectives**
- Compare feedback across 2-3 perspectives
- Identify common concerns
- Strengthen weak areas

### 4. **Iterate Based on Feedback**
- Use feedback to improve content
- Re-test with same perspective
- Compare before/after scores

### 5. **Create Custom Perspectives**
- Don't see your audience? Create one
- Model after existing perspectives
- Customize values and concerns
- Share with team

## Quick Reference Card

```
┌─────────────────────────────────────────────────┐
│ FEEDBACK PERSPECTIVES QUICK GUIDE               │
├─────────────────────────────────────────────────┤
│ Academic US    → Evidence-based, rigorous       │
│ Academic EU    → Theory-heavy, philosophical    │
│ Business UK    → Professional, pragmatic        │
│ Business Asia  → Relationship-focused, harmony  │
│ Startup        → Growth-focused, disruptive     │
│ Community      → Practical, accessible          │
├─────────────────────────────────────────────────┤
│ Try: Start with your actual audience type      │
│      Then test 1-2 adjacent perspectives       │
│      Look for consensus in feedback            │
└─────────────────────────────────────────────────┘
```

---

**Remember: The best feedback comes from matching the perspective to your actual audience!**
