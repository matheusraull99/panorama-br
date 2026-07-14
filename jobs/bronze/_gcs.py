"""Helper compartilhado do Bronze: grava DataFrame como Parquet particionado (Hive) no GCS.

Layout: bronze/{source}/year=AAAA/month=MM/day=DD/{source}_<timestamp>.parquet
Esse layout Hive é lido por tabelas BigLake externas no BigQuery (partition pruning).
"""

from __future__ import annotations

import io
from datetime import UTC, datetime

import pandas as pd


def write_parquet_partitioned(df: pd.DataFrame, bucket_name: str, source: str) -> str:
    """Grava `df` como Parquet no GCS, particionado por data de ingestão. Retorna o URI gs://."""
    from google.cloud import storage  # import tardio p/ facilitar teste local sem credenciais

    now = datetime.now(UTC)
    path = (
        f"bronze/{source}/year={now:%Y}/month={now:%m}/day={now:%d}/"
        f"{source}_{now:%Y%m%d%H%M%S}.parquet"
    )
    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow", index=False)
    buffer.seek(0)

    storage.Client().bucket(bucket_name).blob(path).upload_from_file(
        buffer, content_type="application/octet-stream"
    )
    return f"gs://{bucket_name}/{path}"
