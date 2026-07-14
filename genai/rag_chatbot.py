"""Camada GenAI — Chatbot RAG "Pergunte ao Panorama BR".

Responde perguntas em linguagem natural sobre os dados. Estratégia:
  1. Indexa metadados/dicionário das tabelas Gold num vector DB (Chroma/FAISS).
  2. Recupera o contexto relevante à pergunta (RAG).
  3. LLM gera SQL (NL→SQL) contra o BigQuery, executa e resume a resposta em português.

Esqueleto (Fase 4) — cobre a lacuna GenAI/RAG pedida pelo mercado.
"""

from __future__ import annotations

# TODO(Fase 4):
#   - carregar dicionário de dados (schema + descrições das tabelas Gold)
#   - embeddings + Chroma/FAISS
#   - prompt NL->SQL com guarda-corpos (só SELECT, dataset gold, LIMIT)
#   - executar no BigQuery e resumir com o LLM (Gemini/Claude)


def answer(question: str) -> str:
    raise NotImplementedError("rag_chatbot: implementar na Fase 4")


if __name__ == "__main__":
    print(answer("Qual foi a variação do IPCA nos últimos 12 meses?"))
