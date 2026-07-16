# Dashboard — Panorama Macro BR (Looker Studio)

Especificação do dashboard público que consome as tabelas Gold. Conectar quando o projeto
GCP estiver provisionado (Looker Studio → BigQuery → dataset `gold`).

## Fonte

- `gold.indicadores_mensais` — 1 linha por mês: Selic, câmbio (médio/fim), IPCA mensal e 12m
- `gold.populacao_brasil` — 1 linha por ano

> Gold é `type: "table"` justamente porque o Looker opera em DirectQuery: cada visual
> dispara uma query; tabela materializada = custo fixo e resposta rápida.

## Layout (1 página)

| Bloco | Visual | Campos |
|-------|--------|--------|
| Scorecards (topo) | 4 cartões | Selic atual · IPCA 12m · Câmbio fim do mês · População |
| Inflação | Série temporal c/ 2 eixos | `ipca_mensal` (barras) + `ipca_acumulado_12m` (linha) |
| Juros | Série temporal degrau | `selic_meta_fim_mes` |
| Câmbio | Série temporal | `cambio_usd_medio` + banda com `cambio_usd_fim_mes` |
| Demografia | Coluna + linha | `populacao` + `crescimento_pct` |
| Filtro | Controle de período | `mes` (default: últimos 5 anos) |

## Validação da métrica principal

`ipca_acumulado_12m` (produto composto via `EXP(SUM(LN(1+v/100)))`) foi validado contra a
série oficial do BACEN **13522** (IPCA acumulado 12m): diferença máxima de **0,005 p.p.**
nos últimos 24 meses (apenas arredondamento da série oficial, 2 casas).

## Publicação

1. Looker Studio → Criar → Fonte de dados → BigQuery → `gold.indicadores_mensais`
2. Montar visuais conforme tabela acima
3. Compartilhar → "Qualquer pessoa com o link pode visualizar"
4. Colar o link público no README (badge/section "Dashboard")
