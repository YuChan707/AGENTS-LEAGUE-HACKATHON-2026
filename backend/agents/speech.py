import re

FILLERS = {
    "um", "uh", "like", "you know", "basically",
    "literally", "right", "so", "actually", "anyway"
}

def analyze_speech(text: str, elapsed_seconds: float = 1.0) -> dict:
    words = text.lower().split()
    word_count = len(words)
    filler_hits = [w for w in words if w in FILLERS]
    pace_wpm = int((word_count / max(elapsed_seconds, 1)) * 60)

    sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
    avg_sentence_len = (
        sum(len(s.split()) for s in sentences) / len(sentences)
        if sentences else 0
    )
    clarity = max(0.0, min(1.0, 1.0 - (len(filler_hits) / max(word_count, 1)) * 3))

    return {
        "agent": "speech",
        "type": "speech",
        "payload": {
            "pace_wpm": pace_wpm,
            "filler_count": len(filler_hits),
            "filler_words": list(set(filler_hits)),
            "word_count": word_count,
            "clarity_score": round(clarity, 2),
            "avg_sentence_length": round(avg_sentence_len, 1),
        }
    }
