"""Camada GenAI — Agente de relatório macroeconômico semanal.

Lê as tabelas Gold, monta um resumo dos principais indicadores (Selic, IPCA, câmbio) e pede
ao LLM que escreva um panorama em português, publicado no dashboard / README.

Esqueleto (Fase 4).
"""

from __future__ import annotations

# TODO(Fase 4):
#   - query resumo no BigQuery (últimos N meses por indicador)
#   - montar prompt com os números + instrução de estilo (jornalístico, factual)
#   - gerar texto com LLM e salvar em docs/relatorios/AAAA-MM-DD.md


def generate_report() -> str:
    raise NotImplementedError("weekly_report_agent: implementar na Fase 4")


if __name__ == "__main__":
    print(generate_report())
