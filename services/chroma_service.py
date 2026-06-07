
import os
import chromadb
from chromadb.config import Settings

class ChromaService:
    """
    Local vector database for cultural communication norms.
    Runs in-process — no separate server needed for the hackathon.
    """

    def __init__(self):
        # Persistent local storage — survives restarts
        self.client = chromadb.PersistentClient(
            path="./chroma_data",
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="cultural_norms",
            metadata={"hnsw:space": "cosine"}  # cosine similarity for text
        )

    def seed(self) -> None:
        """
        Load cultural norms knowledge base.
        Call once at startup if collection is empty.
        Maps to your three focus areas: Marketing | Finance | Business
        """
        if self.collection.count() > 0:
            return  # already seeded

        documents = [
            # ── US ────────────────────────────────────────
            "US investor context marketing: direct ROI focus, data visualization preferred, "
            "short attention for narrative, respond to social proof and traction metrics",

            "US executive context finance: bottom-line first, bullet points over paragraphs, "
            "numbers before story, comfortable with interruption, values time efficiency",

            "US customer context business: casual tone acceptable, humor engages, "
            "avoid jargon, concrete benefits over features, testimonials effective",

            # ── Japan ─────────────────────────────────────
            "Japan executive context business: indirect communication required, "
            "consensus building expected, avoid public disagreement, formal honorifics, "
            "silence is positive engagement not disinterest",

            "Japan investor context finance: long-term relationship valued over quick close, "
            "group decision making, detailed written materials expected, "
            "avoid aggressive sales tactics",

            # ── UK ────────────────────────────────────────
            "UK executive context business: understatement is praise, "
            "dry humor signals comfort, direct criticism wrapped in politeness, "
            "avoid American enthusiasm register, self-deprecation builds trust",

            "UK investor context finance: skepticism signals engagement not rejection, "
            "technical depth respected, avoid overselling, "
            "understate projections then exceed them",

            # ── Germany ───────────────────────────────────
            "Germany business context finance: technical precision required, "
            "punctuality is respect, formal address until invited otherwise, "
            "detailed specification documents expected before decision",

            "Germany customer context marketing: quality over price messaging, "
            "engineering credentials matter, avoid emotional appeals, "
            "certification and standards references build trust",

            # ── Marketing signals (cross-region) ──────────
            "Marketing audience engagement: visual storytelling increases retention, "
            "emotional narrative before data, brand consistency signals reliability, "
            "social proof from peer group most effective",

            # ── Finance signals (cross-region) ────────────
            "Finance audience skepticism: challenge assumptions with specifics, "
            "cite sources for projections, acknowledge risks before investor does, "
            "comparable company benchmarks reduce perceived risk",

            # ── Business signals (cross-region) ───────────
            "Business audience decision readiness: clear next step required at close, "
            "decision criteria stated explicitly, timeline and ownership assigned, "
            "executive summary under 3 minutes",
        ]

        ids = [f"norm_{i}" for i in range(len(documents))]
        metadatas = [
            {"region": "us",   "focus": "marketing", "persona": "investor"},
            {"region": "us",   "focus": "finance",   "persona": "executive"},
            {"region": "us",   "focus": "business",  "persona": "customer"},
            {"region": "jp",   "focus": "business",  "persona": "executive"},
            {"region": "jp",   "focus": "finance",   "persona": "investor"},
            {"region": "uk",   "focus": "business",  "persona": "executive"},
            {"region": "uk",   "focus": "finance",   "persona": "investor"},
            {"region": "de",   "focus": "finance",   "persona": "executive"},
            {"region": "de",   "focus": "marketing", "persona": "customer"},
            {"region": "all",  "focus": "marketing", "persona": "all"},
            {"region": "all",  "focus": "finance",   "persona": "all"},
            {"region": "all",  "focus": "business",  "persona": "all"},
        ]

        self.collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
        print(f"ChromaDB seeded with {len(documents)} cultural norm documents")

    def query(
        self,
        region: str,
        persona: str,
        focus_area: str,
        text: str,
        n_results: int = 2
    ) -> list[str]:
        """
        Retrieve top matching cultural norms for the current context.
        Returns list of relevant norm strings to inject into agent prompts.
        """
        results = self.collection.query(
            query_texts=[f"{region} {persona} {focus_area} {text}"],
            n_results=n_results,
            where_document={"$contains": region} if region != "all" else None
        )

        docs = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]

        # Only return results above similarity threshold (distance < 0.6)
        filtered = [
            doc for doc, dist in zip(docs, distances)
            if dist < 0.6
        ]
        return filtered[:2]  # max 2 to keep prompt tokens low


# Singleton — import this everywhere
chroma = ChromaService()