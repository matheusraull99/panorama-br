"""Cliente Gemini (free tier) com escada de fallback de modelos.

Usa o SDK oficial `google-genai`. O free tier bloqueia/limita modelos conforme
disponibilidade; a escada tenta na ordem e fixa no primeiro que responder.
Override via env `GEMINI_MODEL`.
"""

from __future__ import annotations

import os

from google import genai

# Ordem de preferência no free tier (o primeiro que responder vira o modelo da sessão).
MODEL_LADDER = (
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
)

# Escada de embeddings (free tier muda a oferta com o tempo — mesmo racional dos modelos).
EMBEDDING_LADDER = ("gemini-embedding-001", "gemini-embedding-2")

_client: genai.Client | None = None
_active_model: str | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])  # strict — sem fallback
    return _client


def generate(prompt: str) -> str:
    """Gera texto tentando os modelos da escada; fixa no primeiro que funcionar."""
    global _active_model
    client = _get_client()
    ladder = (os.environ.get("GEMINI_MODEL"), _active_model, *MODEL_LADDER)
    last_error: Exception | None = None
    for model_name in dict.fromkeys(m for m in ladder if m):
        try:
            resp = client.models.generate_content(model=model_name, contents=prompt)
            _active_model = model_name
            return resp.text
        except Exception as exc:  # noqa: BLE001 — qualquer erro de modelo cai pro próximo degrau
            print(f"[llm] modelo {model_name} falhou ({type(exc).__name__}); tentando próximo")
            last_error = exc
    raise RuntimeError(f"todos os modelos da escada falharam: {last_error}")


def embed(texts: list[str]) -> list[list[float]]:
    """Embeddings para RAG (dicionário de dados pequeno — chamada única)."""
    client = _get_client()
    last_error: Exception | None = None
    for model_name in EMBEDDING_LADDER:
        try:
            resp = client.models.embed_content(model=model_name, contents=texts)
            return [e.values for e in resp.embeddings]
        except Exception as exc:  # noqa: BLE001
            print(f"[llm] embedding {model_name} falhou ({type(exc).__name__}); tentando próximo")
            last_error = exc
    raise RuntimeError(f"todos os modelos de embedding falharam: {last_error}")
