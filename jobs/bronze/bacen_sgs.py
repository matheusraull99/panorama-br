"""Extrator Bronze — Banco Central do Brasil, API SGS (Sistema Gerenciador de Séries Temporais).

Lê séries temporais macroeconômicas (Selic, IPCA, câmbio) e grava Parquet particionado
(Hive: year/month/day) no GCS, de onde uma tabela BigLake externa lê no BigQuery.

Padrão fail-loud: se a API não devolver dados após retries, `sys.exit(1)` (dispara alerta).
Nunca tratar falha de API como "sem dados".

Uso local:
    GCP_PROJECT_ID=meu-projeto BUCKET_NAME=meu-bucket python -m jobs.bronze.bacen_sgs
"""

from __future__ import annotations

import os
import sys
import time
from datetime import date

import pandas as pd
import requests

from jobs.bronze._gcs import write_parquet_partitioned

SOURCE = "bacen_sgs"

# Séries SGS de interesse (código -> nome). https://dadosabertos.bcb.gov.br/
SERIES: dict[int, str] = {
    432: "selic_meta",
    433: "ipca_mensal",
    1: "cambio_usd_venda",
}

SGS_URL = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
    "?formato=json&dataInicial={ini}&dataFinal={fim}"
)
# A API do BCB responde 406 (content negotiation) sem Accept explícito.
HEADERS = {
    "User-Agent": "panorama-br/1.0 (+https://github.com/matheusraull99/panorama-br)",
    "Accept": "application/json",
}
# Séries diárias (ex: Selic 432, câmbio 1) aceitam janela de no máximo 10 anos.
JANELA_ANOS = 10
MAX_RETRIES = 4
TIMEOUT = 30


def _janela() -> tuple[str, str]:
    hoje = date.today()
    ini = hoje.replace(year=hoje.year - JANELA_ANOS)
    return ini.strftime("%d/%m/%Y"), hoje.strftime("%d/%m/%Y")


def fetch_serie(codigo: int) -> list[dict] | None:
    """Busca uma série do SGS com retries. Retorna None se falhar após todas as tentativas."""
    ini, fim = _janela()
    url = SGS_URL.format(codigo=codigo, ini=ini, fim=fim)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list) or not data:
                raise ValueError(f"resposta inesperada: {str(data)[:120]}")
            return data
        except (requests.RequestException, ValueError) as exc:
            print(f"[{SOURCE}] série {codigo} tentativa {attempt}/{MAX_RETRIES} falhou: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(2 * attempt)  # backoff simples p/ 406 intermitente
    return None


def build_dataframe() -> pd.DataFrame:
    """Monta o DataFrame consolidado de todas as séries. Fail-loud em falha real de API."""
    frames: list[pd.DataFrame] = []
    for codigo, nome in SERIES.items():
        data = fetch_serie(codigo)
        if data is None:
            print(f"[{SOURCE}] ERRO FATAL: série {codigo} ({nome}) sem dados após retries.")
            sys.exit(1)
        df = pd.DataFrame(data)
        df["codigo"] = codigo
        df["serie"] = nome
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
