"""Agente de relatório macroeconômico semanal.

Monta a visão mensal dos indicadores (mesma lógica da Gold `indicadores_mensais`) e pede ao
LLM um panorama em português, salvo em docs/relatorios/AAAA-MM-DD.md.

Funciona em dois modos:
  - GCP: lê direto de `gold.indicadores_mensais` no BigQuery (GOOGLE_CLOUD_PROJECT definido);
  - local: reconstrói os indicadores em pandas a partir das APIs públicas (sem GCP).

Uso:
    GEMINI_API_KEY=... python -m genai.weekly_report_agent
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from genai import llm

REPORT_PROMPT = """Você é um analista macroeconômico escrevendo o resumo semanal "Panorama BR".
Com base APENAS nos dados abaixo (últimos 12 meses), escreva um relatório curto em português:
- título com a data;
- 1 parágrafo de visão geral;
- 3 bullets: inflação (IPCA mensal e acumulado 12m), juros (Selic), câmbio (USD/BRL);
- 1 frase de fechamento sobre a tendência.
Estilo jornalístico, factual, sem recomendação de investimento.

Dados (JSON, 1 linha por mês):
{data}
"""


def load_from_bigquery() -> pd.DataFrame:
    from google.cloud import bigquery

    client = bigquery.Client()
    return client.query(
        "SELECT * FROM gold.indicadores_mensais ORDER BY mes DESC LIMIT 12"
    ).to_dataframe()


def load_local() -> pd.DataFrame:
    """Reconstrói a Gold em pandas a partir das APIs públicas (BACEN)."""
    from jobs.bronze import bacen_sgs

    df = bacen_sgs.build_dataframe()
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["valor"] = df["valor"].astype(float)
    df["mes"] = df["data"].values.astype("datetime64[M]")

    def _por_mes(grupo: pd.DataFrame) -> pd.Series:
        selic = grupo[grupo.serie == "selic_meta"].sort_values("data")["valor"]
        cambio = grupo[grupo.serie == "cambio_usd_venda"]["valor"]
        ipca = grupo[grupo.serie == "ipca_mensal"]["valor"]
        return pd.Series(
            {
                "selic_meta_fim_mes": selic.iloc[-1] if len(selic) else np.nan,
                "cambio_usd_medio": round(cambio.mean(), 4) if len(cambio) else np.nan,
                "ipca_mensal": ipca.max() if len(ipca) else np.nan,
            }
        )

    mensal = df.groupby("mes").apply(_por_mes, include_groups=False).reset_index()
    mensal = mensal.sort_values("mes")
    mensal["ipca_acumulado_12m"] = (
        (np.exp(np.log1p(mensal["ipca_mensal"] / 100).rolling(12).sum()) - 1) * 100
    ).round(2)
    mensal["mes"] = mensal["mes"].dt.strftime("%Y-%m")
    return mensal.dropna(subset=["ipca_mensal"]).tail(12)


def generate_report() -> str:
    df = load_from_bigquery() if os.environ.get("GOOGLE_CLOUD_PROJECT") else load_local()
    return llm.generate(REPORT_PROMPT.format(data=df.to_json(orient="records")))


def main() -> None:
    report = generate_report()
    out_dir = Path(__file__).resolve().parent.parent / "docs" / "relatorios"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{datetime.now(UTC):%Y-%m-%d}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"[weekly_report] salvo em {out_path}\n\n{report}")


if __name__ == "__main__":
    main()
