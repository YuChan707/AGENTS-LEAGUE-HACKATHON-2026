"""Cliente de LLM para el data_processor.

La audiencia sintetica se genera con un modelo LLAMA 3B *dockerizado*. Este
cliente abstrae COMO se llega a ese modelo y degrada con elegancia para que el
pipeline corra siempre (incluso sin sidecar de Dapr ni contenedor levantado):

  transport = "dapr"  -> Dapr Conversation API (converse_alpha1) contra un
                          componente `conversation.*` que apunta al Llama
                          dockerizado. Es el camino "Llama via dapr agents".
  transport = "http"  -> endpoint OpenAI-compatible del contenedor (Ollama,
                          llama.cpp server, vLLM...). POST /chat/completions.
  transport = "mock"  -> sin red: el llamador provee un fixture valido. Sirve
                          para demo/CI y para no romper si el modelo no esta.

`transport = "auto"` (default) intenta dapr -> http y, si ambos fallan, deja
que el llamador caiga al mock. La seleccion se controla por entorno:

    LLM_TRANSPORT      auto | dapr | http | mock        (default: auto)
    DAPR_LLM_COMPONENT nombre del componente Dapr        (default: llama)
    LLAMA_BASE_URL     base OpenAI-compatible            (default: http://localhost:11434/v1)
    LLAMA_MODEL        nombre del modelo                 (default: llama3.2:3b)
    LLAMA_API_KEY      token (Ollama no lo exige)        (default: ollama)
    LLM_TEMPERATURE    temperatura de muestreo           (default: 0.4)
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass


class LLMUnavailable(RuntimeError):
    """Ningun transporte real (dapr/http) pudo responder."""


def _env(name: str, default: str) -> str:
    val = os.getenv(name)
    return val if val not in (None, "") else default


# ---------------------------------------------------------------------------
# Extraccion de JSON: los modelos pequenos suelen envolver el JSON en ``` o
# anteponer texto. Recuperamos el primer objeto/array balanceado.
# ---------------------------------------------------------------------------
_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def extract_json(text: str):
    """Devuelve el primer objeto/array JSON encontrado en `text`.

    Tolera fences markdown y prosa antes/despues. Lanza ValueError si no hay
    JSON parseable.
    """
    if not text or not text.strip():
        raise ValueError("respuesta vacia del modelo")

    candidates = []
    m = _FENCE.search(text)
    if m:
        candidates.append(m.group(1))
    candidates.append(text)

    for chunk in candidates:
        chunk = chunk.strip()
        try:
            return json.loads(chunk)
        except json.JSONDecodeError:
            pass
        # Buscar el primer { o [ y recortar hasta su cierre balanceado.
        start = min(
            [i for i in (chunk.find("{"), chunk.find("[")) if i != -1],
            default=-1,
        )
        if start == -1:
            continue
        snippet = _balanced_slice(chunk, start)
        if snippet:
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                continue
    raise ValueError("no se encontro JSON valido en la respuesta del modelo")


def _balanced_slice(text: str, start: int) -> str | None:
    """Recorta desde `start` hasta cerrar el delimitador, respetando strings."""
    open_ch = text[start]
    close_ch = "}" if open_ch == "{" else "]"
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


@dataclass
class LlamaClient:
    """Cliente unificado hacia el Llama dockerizado."""

    transport: str = ""
    model: str = ""
    dapr_component: str = ""
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0.4

    def __post_init__(self) -> None:
        self.transport = (self.transport or _env("LLM_TRANSPORT", "auto")).lower()
        self.model = self.model or _env("LLAMA_MODEL", "llama3.2:3b")
        self.dapr_component = self.dapr_component or _env("DAPR_LLM_COMPONENT", "llama")
        self.base_url = (self.base_url or _env("LLAMA_BASE_URL", "http://localhost:11434/v1")).rstrip("/")
        self.api_key = self.api_key or _env("LLAMA_API_KEY", "ollama")
        if not self.temperature:
            self.temperature = float(_env("LLM_TEMPERATURE", "0.4"))

    # -- API publica --------------------------------------------------------
    def complete(self, system: str, user: str) -> str:
        """Devuelve el texto crudo del modelo. Lanza LLMUnavailable si no hay
        transporte real disponible (el llamador decide si cae al mock)."""
        # En "auto" solo intentamos Dapr si hay un sidecar (evita el health check
        # de 60s cuando no se corre con `dapr run`). En "dapr" explicito siempre
        # se intenta, pero con health check rapido para fallar pronto.
        auto = ["http"]
        if os.getenv("DAPR_GRPC_PORT") or os.getenv("DAPR_HTTP_PORT"):
            auto = ["dapr", "http"]
        order = {
            "dapr": ["dapr"],
            "http": ["http"],
            "mock": [],
            "auto": auto,
        }.get(self.transport, auto)

        errors = []
        for t in order:
            try:
                if t == "dapr":
                    return self._via_dapr(system, user)
                if t == "http":
                    return self._via_http(system, user)
            except Exception as exc:  # noqa: BLE001 - degradamos a la siguiente opcion
                errors.append(f"{t}: {type(exc).__name__}: {exc}")
        raise LLMUnavailable(
            f"sin transporte LLM disponible (transport={self.transport}). " + " | ".join(errors)
        )

    @property
    def is_mock(self) -> bool:
        return self.transport == "mock"

    # -- Transportes --------------------------------------------------------
    def _via_dapr(self, system: str, user: str) -> str:
        # Health check rapido: si el sidecar no esta, fallamos en segundos (no 60s).
        os.environ.setdefault("DAPR_HEALTH_TIMEOUT", _env("DAPR_HEALTH_TIMEOUT", "5"))
        from dapr.clients import DaprClient
        from dapr.clients.grpc.conversation import ConversationInput

        inputs = [
            ConversationInput(content=system, role="system"),
            ConversationInput(content=user, role="user"),
        ]
        with DaprClient() as client:
            resp = client.converse_alpha1(
                name=self.dapr_component,
                inputs=inputs,
                temperature=self.temperature,
            )
        parts = [o.result for o in (resp.outputs or []) if getattr(o, "result", None)]
        text = "\n".join(parts).strip()
        if not text:
            raise LLMUnavailable("Dapr devolvio respuesta vacia")
        return text

    def _via_http(self, system: str, user: str) -> str:
        import httpx

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature,
            "stream": False,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        with httpx.Client(timeout=120) as http:
            r = http.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        if not text:
            raise LLMUnavailable("endpoint HTTP devolvio respuesta vacia")
        return text


__all__ = ["LlamaClient", "LLMUnavailable", "extract_json"]
