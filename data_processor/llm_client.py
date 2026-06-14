"""LLM client for the data_processor.

The synthetic audience is generated with a *dockerized* LLAMA 3B model. This
client abstracts HOW that model is reached and degrades gracefully so that the
pipeline always runs (even without a Dapr sidecar or a running container):

  transport = "dapr"  -> Dapr Conversation API (converse_alpha1) against a
                          `conversation.*` component that points at the
                          dockerized Llama. This is the "Llama via dapr agents"
                          path.
  transport = "http"  -> OpenAI-compatible endpoint of the container (Ollama,
                          llama.cpp server, vLLM...). POST /chat/completions.
  transport = "mock"  -> no network: the caller provides a valid fixture. Useful
                          for demo/CI and to avoid breaking if the model is down.

`transport = "auto"` (default) tries dapr -> http and, if both fail, lets the
caller fall back to the mock. The selection is controlled by the environment:

    LLM_TRANSPORT      auto | dapr | http | mock        (default: auto)
    DAPR_LLM_COMPONENT Dapr component name               (default: llama)
    LLAMA_BASE_URL     OpenAI-compatible base            (default: http://localhost:11434/v1)
    LLAMA_MODEL        model name                        (default: llama3.2:3b)
    LLAMA_API_KEY      token (Ollama does not require it) (default: ollama)
    LLM_TEMPERATURE    sampling temperature              (default: 0.4)
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass


class LLMUnavailable(RuntimeError):
    """No real transport (dapr/http) was able to respond."""


def _env(name: str, default: str) -> str:
    val = os.getenv(name)
    return val if val not in (None, "") else default


# ---------------------------------------------------------------------------
# JSON extraction: small models often wrap the JSON in ``` or prepend text.
# We recover the first balanced object/array.
# ---------------------------------------------------------------------------
_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def extract_json(text: str):
    """Return the first JSON object/array found in `text`.

    Tolerates markdown fences and prose before/after. Raises ValueError if there
    is no parseable JSON.
    """
    if not text or not text.strip():
        raise ValueError("empty response from the model")

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
        # Find the first { or [ and trim up to its balanced close.
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
    raise ValueError("no valid JSON found in the model's response")


def _balanced_slice(text: str, start: int) -> str | None:
    """Trim from `start` until the delimiter closes, respecting strings."""
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
    """Unified client toward the dockerized Llama."""

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

    # -- public API ---------------------------------------------------------
    def complete(self, system: str, user: str) -> str:
        """Return the raw text from the model. Raises LLMUnavailable if no real
        transport is available (the caller decides whether to fall back to the
        mock)."""
        # In "auto" we only try Dapr if there is a sidecar (avoids the 60s health
        # check when not running with `dapr run`). In explicit "dapr" it is always
        # tried, but with a fast health check to fail early.
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
            except Exception as exc:  # noqa: BLE001 - degrade to the next option
                errors.append(f"{t}: {type(exc).__name__}: {exc}")
        raise LLMUnavailable(
            f"no LLM transport available (transport={self.transport}). " + " | ".join(errors)
        )

    @property
    def is_mock(self) -> bool:
        return self.transport == "mock"

    # -- Transports ---------------------------------------------------------
    def _via_dapr(self, system: str, user: str) -> str:
        # Fast health check: if the sidecar is down, we fail in seconds (not 60s).
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
            raise LLMUnavailable("Dapr returned an empty response")
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
            raise LLMUnavailable("HTTP endpoint returned an empty response")
        return text


__all__ = ["LlamaClient", "LLMUnavailable", "extract_json"]
