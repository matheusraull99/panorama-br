"""Dicionário de dados das tabelas Gold — a base de conhecimento do RAG.

Cada entrada vira um documento embedado no vector store; o chatbot recupera os mais
relevantes à pergunta e monta o contexto do prompt NL→SQL.
"""

from __future__ import annotations

CATALOG: list[dict] = [
    {
        "table": "gold.indicadores_mensais",
        "doc": (
            "Tabela gold.indicadores_mensais — indicadores macroeconômicos do Brasil por mês. "
            "Colunas: mes (DATE, primeiro dia do mês); selic_meta_fim_mes (FLOAT64, meta da taxa "
            "Selic vigente no fim do mês, % ao ano); cambio_usd_medio (FLOAT64, câmbio dólar/real "
            "médio do mês, venda); cambio_usd_fim_mes (FLOAT64, câmbio do último dia útil); "
            "ipca_mensal (FLOAT64, inflação IPCA variação mensal %); ipca_acumulado_12m (FLOAT64, "
            "IPCA acumulado em 12 meses %). Perguntas típicas: inflação atual, IPCA acumulado, "
            "quanto está a Selic, cotação do dólar, evolução do câmbio."
        ),
    },
    {
        "table": "gold.populacao_brasil",
        "doc": (
            "Tabela gold.populacao_brasil — população residente estimada do Brasil por ano "
            "(IBGE/SIDRA tabela 6579). Colunas: ano (INT64); populacao (INT64, habitantes); "
            "crescimento_pct (FLOAT64, crescimento % vs ano anterior). Perguntas típicas: "
            "quantos habitantes tem o Brasil, crescimento populacional."
        ),
    },
]
