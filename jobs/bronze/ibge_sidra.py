"""Extrator Bronze — IBGE, API SIDRA (agregados: PIB, população, inflação).

Esqueleto (Fase 1). Segue o mesmo padrão do `bacen_sgs`: fetch com retries → fail-loud →
Parquet particionado no GCS → BigLake.

Doc: https://apisidra.ibge.gov.br/
"""

from __future__ import annotations

# TODO(Fase 1): implementar seguindo o padrão de jobs/bronze/bacen_sgs.py
#   - tabelas SIDRA de interesse (ex: 6784 PIB, 6579 população estimada)
#   - fetch_agregado(tabela) com retries + fail-loud (sys.exit(1))
#   - gravar Parquet em bronze/ibge_sidra/year=.../month=.../day=...


def main() -> None:
    raise NotImplementedError("ibge_sidra: implementar na Fase 1")


if __name__ == "__main__":
    main()
