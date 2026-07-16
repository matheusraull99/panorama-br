// Declaração das tabelas Bronze (BigLake) que o Dataform lê.
// As tabelas físicas são criadas via Terraform; aqui só declaramos para o `${ref()}`.

const BRONZE_DATASET = "bronze";

const sources = ["bacen_sgs", "ibge_sidra"];

sources.forEach((name) => {
  declare({
    schema: BRONZE_DATASET,
    name: name,
  });
});

// Saída do job PySpark (spark/silver_rolling_stats.py), lida como source pelo Silver.
declare({
  schema: "silver_spark",
  name: "sgs_rolling",
});
