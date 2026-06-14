"""
Returns an async OpenAI-compatible chat client.

Priority:
  1. Azure OpenAI  — when AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_KEY are set
  2. Groq          — when GROQ_API_KEY is set (default for local dev)

Both clients expose the same AsyncOpenAI interface so callers don't change.
"""
import os
from openai import AsyncAzureOpenAI, AsyncOpenAI


def get_llm_client() -> AsyncOpenAI:
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
    azure_key = os.getenv("AZURE_OPENAI_KEY", "").strip()

    if azure_endpoint and azure_key:
        return AsyncAzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_key,
            api_version="2024-02-01",
        )

    # Fall back to Groq (OpenAI-compatible endpoint)
    return AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY", ""),
    )


def get_model(fast: bool = True) -> str:
    """Return the appropriate model name for the active backend."""
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
    if azure_endpoint:
        return os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    # Groq model names
    return "llama-3.1-8b-instant" if fast else "llama-3.3-70b-versatile"
