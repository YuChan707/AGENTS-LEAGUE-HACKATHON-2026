import chromadb
from chromadb.config import Settings

class ChromaService:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path="./chroma_data",
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="cultural_norms",
            metadata={"hnsw:space": "cosine"}
        )

    def seed(self):
        if self.collection.count() > 0:
            return
        docs = [
            "US investor context marketing: direct ROI focus, data visualization preferred, respond to traction metrics",
            "US executive context finance: bottom-line first, bullet points, numbers before story, values time",
            "US customer context business: casual tone, concrete benefits over features, testimonials effective",
            "Japan executive context business: indirect communication, consensus building, avoid public disagreement",
            "Japan investor context finance: long-term relationship valued, group decision making, detailed materials expected",
            "UK executive context business: understatement is praise, dry humor signals comfort, avoid overselling",
            "UK investor context finance: skepticism signals engagement, technical depth respected",
            "Germany business context finance: technical precision required, formal address, detailed specs before decision",
            "Germany customer context marketing: quality over price, engineering credentials matter",
            "Marketing audience: emotional narrative before data, social proof effective, visual storytelling",
            "Finance audience: challenge assumptions with specifics, cite sources, acknowledge risks proactively",
            "Business audience: clear next step required, decision criteria stated explicitly, executive summary under 3 minutes",
        ]
        ids = [f"norm_{i}" for i in range(len(docs))]
        self.collection.add(documents=docs, ids=ids)
        print(f"ChromaDB seeded with {len(docs)} documents")

    def query(self, region: str, persona: str, focus_area: str, text: str) -> list[str]:
        results = self.collection.query(
            query_texts=[f"{region} {persona} {focus_area} {text}"],
            n_results=2
        )
        docs = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        return [d for d, dist in zip(docs, distances) if dist < 0.6]

chroma = ChromaService()
