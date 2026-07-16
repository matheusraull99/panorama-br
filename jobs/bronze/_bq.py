"""Sink alternativo do Bronze: carga direta em tabela nativa do BigQuery.

Usado no modo "sandbox" (sem conta de faturamento): o BigQuery sandbox aceita load jobs
gratuitos, dispensando GCS/BigLake. As colunas de partição de ingestão (year/month/day)
são adicionadas aqui para manter os modelos Silver idênticos nos dois modos.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd


def load_dataframe(df: pd.DataFrame, project: str, table: str) -> str:
    """Anexa `df` em `project.bronze.{table}` com colunas de ingestão. Retorna o destino."""
    from google.cloud import bigquery

    now = datetime.now(UTC)
    df = df.copy()
    df["year"] = now.year
    df["month"] = now.month
    df["day"] = now.day

    client = bigquery.Client(project=project)
    destination = f"{project}.bronze.{table}"
    # WRITE_TRUNCATE (modo sandbox): as fontes entregam a janela completa a cada extração,
    # então substituir mantém o Bronze enxuto E renova a expiração de 60 dias do sandbox.
    # No modo completo (GCS/BigLake) o histórico bruto fica no Parquet particionado.
    job = client.load_table_from_dataframe(
        df,
        destination,
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"),
    )
    job.result()
    return destination
