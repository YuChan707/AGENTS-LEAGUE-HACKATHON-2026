"""Foundry IQ: capa de *grounding* (conocimiento) para la generacion sintetica.

Foundry IQ (Microsoft / Azure AI Foundry) es la capa de recuperacion agentica
de conocimiento. Aqui la usamos para ANCLAR la audiencia sintetica en hechos
reales antes de pedirsela al Llama dockerizado: el modelo no inventa en el
vacio, razona sobre evidencia recuperada.

Dos modos, igual que el cliente LLM:

  * Azure AI Foundry IQ  -> si hay endpoint configurado, hace retrieval contra
    una knowledge source de Foundry IQ y devuelve los pasajes recuperados.
      FOUNDRY_IQ_ENDPOINT        base del recurso de Foundry
      FOUNDRY_IQ_API_KEY         api key / token
      FOUNDRY_IQ_KNOWLEDGE_BASE  id de la knowledge source / agente de retrieval

  * Local (default)      -> aterriza el grounding en la ESTADISTICA REAL de la
    ubicacion (Census ACS5 ya ingerido). Esta data ES evidencia real, asi que
    el pipeline siempre queda anclado aunque no haya servicio Foundry.

`ground(query, location_stats)` devuelve un bloque de texto listo para anexar
al prompt del modelo.
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
        """True si hay un recurso Foundry IQ remoto configurado."""
        return bool(self.endpoint and self.api_key and self.knowledge_base)

    def ground(self, query: str, location_stats: dict | None = None) -> str:
        """Devuelve un bloque de grounding (texto) para anexar al prompt."""
        passages: list[str] = []
        if self.enabled:
            try:
                passages = self._retrieve_remote(query)
            except Exception as exc:  # noqa: BLE001 - degradamos a grounding local
                passages = [f"(Foundry IQ remoto no disponible: {type(exc).__name__})"]
        passages += self._ground_local(location_stats)

        if not passages:
            return ""
        body = "\n".join(f"- {p}" for p in passages)
        return (
            "EVIDENCIA DE GROUNDING (Foundry IQ — usala como hechos, no la "
            f"contradigas):\n{body}"
        )

    # -- retrieval remoto (Azure AI Foundry IQ) -----------------------------
    def _retrieve_remote(self, query: str) -> list[str]:
        import httpx

        payload = {"knowledgeBase": self.knowledge_base, "query": query, "topK": self.top_k}
        headers = {"Content-Type": "application/json", "api-key": self.api_key}
        with httpx.Client(timeout=60) as http:
            r = http.post(f"{self.endpoint}/retrieve", json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        # Toleramos varias formas de respuesta de retrieval.
        items = data.get("results") or data.get("passages") or data.get("documents") or []
        out = []
        for it in items[: self.top_k]:
            if isinstance(it, str):
                out.append(it)
            elif isinstance(it, dict):
                out.append(it.get("content") or it.get("text") or json.dumps(it, ensure_ascii=False))
        return out

    # -- grounding local sobre estadistica real -----------------------------
    def _ground_local(self, location_stats: dict | None) -> list[str]:
        if not location_stats:
            return []
        s = location_stats
        facts: list[str] = []
        if s.get("median_income") is not None:
            facts.append(f"Ingreso mediano real del hogar: ${s['median_income']} (Census ACS5).")
        if s.get("unemployment_rate") is not None:
            facts.append(f"Tasa de desempleo real: {s['unemployment_rate']}%.")
        if s.get("poverty_rate") is not None:
            facts.append(f"Tasa de pobreza real: {s['poverty_rate']}%.")
        if s.get("ethnicity_distribution"):
            top = sorted(s["ethnicity_distribution"].items(), key=lambda kv: kv[1], reverse=True)
            dist = ", ".join(f"{k} {v:.1f}%" for k, v in top if v)
            facts.append(f"Distribucion etnica real: {dist}.")
        if s.get("age_ranges"):
            ages = ", ".join(f"{k} {v:.1f}%" for k, v in s["age_ranges"].items())
            facts.append(f"Distribucion etaria real: {ages}.")
        if s.get("avg_education") is not None:
            facts.append(f"Indicador educativo real (% bachelor+): {s['avg_education']}.")
        return facts


__all__ = ["FoundryIQ"]
