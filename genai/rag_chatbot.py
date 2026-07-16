"""Chatbot RAG "Pergunte ao Panorama BR" — NL→SQL sobre as tabelas Gold.

Fluxo:
  1. Embeda o dicionário de dados (catalog.py) e a pergunta; recupera as tabelas mais
     relevantes por similaridade de cosseno (RAG).
  2. LLM (Gemini) gera SQL BigQuery **somente SELECT** sobre o dataset gold.
  3. Guarda-corpos validam o SQL (allowlist de tabelas, sem DML/DDL, LIMIT obrigatório).
  4. Executa no BigQuery (se GOOGLE_CLOUD_PROJECT definido) e resume em português.
     Sem projeto GCP, roda em modo offline: devolve o SQL gerado e validado.

Uso:
    GEMINI_API_KEY=... python -m genai.rag_chatbot "Qual o IPCA acumulado em 12 meses?"
"""

from __future__ import annotations

import os
import re
import sys

import numpy as np

from genai import llm
from genai.catalog import CATALOG

ALLOWED_TABLES = {entry["table"] for entry in CATALOG}
FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|CREATE|ALTER|TRUNCATE|GRANT|EXPORT|CALL)\b", re.I
)
DEFAULT_LIMIT = 100

SQL_PROMPT = """Você é um gerador de SQL para BigQuery (SQL padrão).
Gere UMA única query SELECT que responda à pergunta do usuário, usando SOMENTE as tabelas
descritas no contexto abaixo. Regras:
- apenas SELECT (nunca DML/DDL);
- use os nomes de tabela exatamente como no contexto (ex: gold.indicadores_mensais);
- inclua LIMIT {limit} ao final;
- responda SOMENTE com o SQL, sem explicação e sem markdown.

Contexto (dicionário de dados):
{context}

Pergunta: {question}
"""

SUMMARY_PROMPT = """Você é um analista macroeconômico. Responda à pergunta do usuário em
português, em 2-4 frases, usando APENAS os dados abaixo (resultado de uma query SQL).
Cite números com unidade. Seja factual, sem opinião.

Pergunta: {question}
SQL executado: {sql}
Resultado (JSON): {rows}
"""


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def retrieve(question: str, top_k: int = 2) -> list[dict]:
    """RAG: recupera as entradas do catálogo mais similares à pergunta."""
    vectors = llm.embed([question, *[e["doc"] for e in CATALOG]])
    q_vec = np.array(vectors[0])
    scored = [
        (_cosine(q_vec, np.array(vec)), entry)
        for vec, entry in zip(vectors[1:], CATALOG, strict=True)
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [entry for _, entry in scored[:top_k]]


def validate_sql(sql: str) -> str:
    """Guarda-corpos: SELECT-only, allowlist de tabelas, sem múltiplos statements, LIMIT."""
    sql = re.sub(r"^```(sql)?|```$", "", sql.strip(), flags=re.M).strip().rstrip(";")
    if not re.match(r"^\s*(SELECT|WITH)\b", sql, re.I):
        raise ValueError(f"apenas SELECT/WITH é permitido: {sql[:80]}")
    if ";" in sql:
        raise ValueError("múltiplos statements não são permitidos")
    if FORBIDDEN.search(sql):
        raise ValueError("SQL contém operação proibida (DML/DDL)")
    referenced = set(re.findall(r"\b(?:from|join)\s+[`]?([\w.]+)[`]?", sql, re.I))
    unknown = {t for t in referenced if t not in ALLOWED_TABLES}
    if unknown:
        raise ValueError(f"tabelas fora da allowlist: {unknown}")
    if not re.search(r"\bLIMIT\s+\d+\b", sql, re.I):
        sql = f"{sql}\nLIMIT {DEFAULT_LIMIT}"
    return sql


def run_bigquery(sql: str) -> list[dict]:
    from google.cloud import bigquery

    client = bigquery.Client()
    return [dict(row) for row in client.query(sql).result()]


def answer(question: str) -> str:
    context = "\n\n".join(e["doc"] for e in retrieve(question))
    raw_sql = llm.generate(SQL_PROMPT.format(context=context, question=question, limit=DEFAULT_LIMIT))
    sql = validate_sql(raw_sql)

    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        return f"[modo offline — sem GOOGLE_CLOUD_PROJECT]\nSQL gerado e validado:\n{sql}"

    rows = run_bigquery(sql)
    return llm.generate(SUMMARY_PROMPT.format(question=question, sql=sql, rows=rows[:50]))


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or "Qual o IPCA acumulado nos últimos 12 meses?"
    print(answer(pergunta))
