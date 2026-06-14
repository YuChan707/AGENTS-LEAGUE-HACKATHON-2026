"""Foundry IQ: *grounding* (knowledge) layer for synthetic generation.

Foundry IQ (Microsoft / Azure AI Foundry) is the agentic knowledge retrieval
layer. Here we use it to ANCHOR the synthetic audience in real facts before
asking the dockerized Llama for it: the model does not invent in a vacuum, it
reasons over retrieved evidence.

Two modes, just like the LLM client:

  * Azure AI Foundry IQ  -> if an endpoint is configured, it retrieves against
    a Foundry IQ knowledge source and returns the retrieved passages.
      FOUNDRY_IQ_ENDPOINT        base of the Foundry resource
      FOUNDRY_IQ_API_KEY         api key / token
      FOUNDRY_IQ_KNOWLEDGE_BASE  knowledge source / retrieval agent id

  * Local (default)      -> grounds on the REAL STATISTICS of the location
    (already ingested Census ACS5). This data IS real evidence, so the pipeline
    always stays anchored even without a Foundry service.

`ground(query, location_stats)` returns a text block ready to append to the
model's prompt.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass


def _env(name: str, default: str = "") -> str:
    val = os.getenv(name)
    return val if val not in (None, "") else default


@dataclass
class FoundryIQ:
    endpoint: str = ""
    api_key: str = ""
    knowledge_base: str = ""
    top_k: int = 5

    def __post_init__(self) -> None:
        self.endpoint = (self.endpoint or _env("FOUNDRY_IQ_ENDPOINT")).rstrip("/")
        self.api_key = self.api_key or _env("FOUNDRY_IQ_API_KEY")
        self.knowledge_base = self.knowledge_base or _env("FOUNDRY_IQ_KNOWLEDGE_BASE")

    @property
    def enabled(self) -> bool:
        """True if a remote Foundry IQ resource is configured."""
        return bool(self.endpoint and self.api_key and self.knowledge_base)

    def ground(self, query: str, location_stats: dict | None = None) -> str:
        """Return a grounding block (text) to append to the prompt."""
        passages: list[str] = []
        if self.enabled:
            try:
                passages = self._retrieve_remote(query)
            except Exception as exc:  # noqa: BLE001 - degrade to local grounding
                passages = [f"(remote Foundry IQ not available: {type(exc).__name__})"]
        passages += self._ground_local(location_stats)

        if not passages:
            return ""
        body = "\n".join(f"- {p}" for p in passages)
        return (
            "GROUNDING EVIDENCE (Foundry IQ — use it as facts, do not "
            f"contradict it):\n{body}"
        )

    # -- remote retrieval (Azure AI Foundry IQ) -----------------------------
    def _retrieve_remote(self, query: str) -> list[str]:
        import httpx

        payload = {"knowledgeBase": self.knowledge_base, "query": query, "topK": self.top_k}
        headers = {"Content-Type": "application/json", "api-key": self.api_key}
        with httpx.Client(timeout=60) as http:
            r = http.post(f"{self.endpoint}/retrieve", json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        # Tolerate several retrieval response shapes.
        items = data.get("results") or data.get("passages") or data.get("documents") or []
        out = []
        for it in items[: self.top_k]:
            if isinstance(it, str):
                out.append(it)
            elif isinstance(it, dict):
                out.append(it.get("content") or it.get("text") or json.dumps(it, ensure_ascii=False))
        return out

    # -- local grounding over real statistics -------------------------------
    def _ground_local(self, location_stats: dict | None) -> list[str]:
        if not location_stats:
            return []
        s = location_stats
        facts: list[str] = []
        if s.get("median_income") is not None:
            facts.append(f"Real median household income: ${s['median_income']} (Census ACS5).")
        if s.get("unemployment_rate") is not None:
            facts.append(f"Real unemployment rate: {s['unemployment_rate']}%.")
        if s.get("poverty_rate") is not None:
            facts.append(f"Real poverty rate: {s['poverty_rate']}%.")
        if s.get("ethnicity_distribution"):
            top = sorted(s["ethnicity_distribution"].items(), key=lambda kv: kv[1], reverse=True)
            dist = ", ".join(f"{k} {v:.1f}%" for k, v in top if v)
            facts.append(f"Real ethnic distribution: {dist}.")
        if s.get("age_ranges"):
            ages = ", ".join(f"{k} {v:.1f}%" for k, v in s["age_ranges"].items())
            facts.append(f"Real age distribution: {ages}.")
        if s.get("avg_education") is not None:
            facts.append(f"Real education indicator (% bachelor+): {s['avg_education']}.")
        return facts


__all__ = ["FoundryIQ"]
