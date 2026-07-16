"""Extrator Bronze — IBGE, API SIDRA (agregados: população, inflação).

Mesmo padrão do `bacen_sgs`: fetch com retries → fail-loud → Parquet particionado no GCS → BigLake.

A API SIDRA devolve uma lista JSON cujo PRIMEIRO elemento é o cabeçalho (rótulos das colunas);
os demais são as observações. No Bronze guardamos as observações cruas (Silver limpa/tipa).

Doc: https://apisidra.ibge.gov.br/

Uso local:
    GCP_PROJECT_ID=meu-projeto BUCKET_NAME=meu-bucket python -m jobs.bronze.ibge_sidra
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import requests

from jobs.bronze._gcs import write_parquet_partitioned

SOURCE = "ibge_sidra"

# nome -> caminho relativo da consulta SIDRA (após /values)
TABELAS: dict[str, str] = {
    "populacao_estimada": "/t/6579/n1/1/v/9324/p/all",
    "ipca_variacao_mensal": "/t/1737/n1/1/v/63/p/last%2012",
}

BASE_URL = "https://apisidra.ibge.gov.br/values"
HEADERS = {"User-Agent": "panorama-br/1.0 (+https://github.com/matheusraull99/panorama-br)"}
MAX_RETRIES = 3
TIMEOUT = 60


def fetch_tabela(path: str) -> list[dict] | None:
    """Busca uma consulta SIDRA com retries. Retorna None se falhar após todas as tentativas."""
    url = f"{BASE_URL}{path}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            # SIDRA às vezes responde 200 com dict de erro em vez de lista.
            if not isinstance(data, list) or len(data) < 2:
                raise ValueError(f"resposta inesperada: {str(data)[:120]}")
            return data[1:]  # descarta o cabeçalho (índice 0)
        except (requests.RequestException, ValueError) as exc:
            print(f"[{SOURCE}] {path} tentativa {attempt}/{MAX_RETRIES} falhou: {exc}")
    return None


def build_dataframe() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for nome, path in TABELAS.items():
        rows = fetch_tabela(path)
        if rows is None:
            print(f"[{SOURCE}] ERRO FATAL: tabela {nome} ({path}) sem dados após retries.")
            sys.exit(1)
        df = pd.DataFrame(rows)
        df["tabela"] = nome
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    df = build_dataframe()
    if df.empty:
        print(f"[{SOURCE}] ERRO FATAL: DataFrame vazio.")
        sys.exit(1)
    # Sink: GCS/BigLake quando há bucket (Cloud Run); senão BigQuery direto (modo sandbox).
    if bucket_name := os.environ.get("BUCKET_NAME"):
        dest = write_parquet_partitioned(df, bucket_name, SOURCE)
    else:
        from jobs.bronze._bq import load_dataframe

        dest = load_dataframe(df, os.environ["GCP_PROJECT_ID"], SOURCE)
    print(f"[{SOURCE}] OK — {len(df)} linhas gravadas em {dest}")


if __name__ == "__main__":
    main()
