"""Extrator Bronze — Banco Central do Brasil, API SGS (Sistema Gerenciador de Séries Temporais).

Lê séries temporais macroeconômicas (Selic, IPCA, câmbio) e grava Parquet particionado
(Hive: year/month/day) no GCS, de onde uma tabela BigLake externa lê no BigQuery.

Padrão fail-loud: se a API não devolver dados após retries, `sys.exit(1)` (dispara alerta).
Nunca tratar falha de API como "sem dados".

Uso local:
    GCP_PROJECT_ID=meu-projeto BUCKET_NAME=meu-bucket python -m jobs.bronze.bacen_sgs
"""

from __future__ import annotations

import io
import os
import sys
from datetime import datetime, timezone

import pandas as pd
import requests

# Séries SGS de interesse (código -> nome). https://dadosabertos.bcb.gov.br/
SERIES: dict[int, str] = {
    432: "selic_meta",
    433: "ipca_mensal",
    1: "cambio_usd_venda",
}

SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json"
MAX_RETRIES = 3
TIMEOUT = 30


def fetch_serie(codigo: int) -> list[dict] | None:
    """Busca uma série do SGS com retries. Retorna None se falhar após todas as tentativas."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(SGS_URL.format(codigo=codigo), timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            print(f"[bacen_sgs] série {codigo} tentativa {attempt}/{MAX_RETRIES} falhou: {exc}")
    return None


def build_dataframe() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for codigo, nome in SERIES.items():
        data = fetch_serie(codigo)
        if data is None:
            # Fail-loud: falha real de API não é "sem dados".
            print(f"[bacen_sgs] ERRO FATAL: série {codigo} ({nome}) sem dados após retries.")
            sys.exit(1)
        df = pd.DataFrame(data)
        df["codigo"] = codigo
        df["serie"] = nome
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def upload_parquet(df: pd.DataFrame, bucket_name: str) -> str:
    """Grava o DataFrame como Parquet particionado por data de ingestão no GCS."""
    from google.cloud import storage  # import tardio p/ facilitar teste local

    now = datetime.now(timezone.utc)
    path = (
        f"bronze/bacen_sgs/year={now:%Y}/month={now:%m}/day={now:%d}/"
        f"bacen_sgs_{now:%Y%m%d%H%M%S}.parquet"
    )
    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow", index=False)
    buffer.seek(0)

    storage.Client().bucket(bucket_name).blob(path).upload_from_file(
        buffer, content_type="application/octet-stream"
    )
    return f"gs://{bucket_name}/{path}"


def main() -> None:
    bucket_name = os.environ["BUCKET_NAME"]  # strict — sem fallback
    df = build_dataframe()
    if df.empty:
        print("[bacen_sgs] ERRO FATAL: DataFrame vazio.")
        sys.exit(1)
    uri = upload_parquet(df, bucket_name)
    print(f"[bacen_sgs] OK — {len(df)} linhas gravadas em {uri}")


if __name__ == "__main__":
    main()
