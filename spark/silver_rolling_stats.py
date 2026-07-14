"""Silver pesado em PySpark — estatísticas móveis das séries do SGS.

Roda em Databricks Community Edition ou Dataproc Serverless. Lê o Bronze (Parquet no GCS),
calcula médias/desvios móveis (janelas de 3/6/12 meses) por série e grava de volta em
Parquet, que o Dataform materializa como tabela Silver.

Esqueleto (Fase 2) — cobre a lacuna Spark/Databricks pedida pelo mercado.
"""

from __future__ import annotations

# TODO(Fase 2):
#   from pyspark.sql import SparkSession, Window
#   from pyspark.sql import functions as F
#
#   spark = SparkSession.builder.appName("panorama-br-rolling-stats").getOrCreate()
#   df = spark.read.parquet("gs://<bucket>/bronze/bacen_sgs/")
#   w = Window.partitionBy("codigo").orderBy("data").rowsBetween(-2, 0)
#   out = df.withColumn("media_movel_3m", F.avg("valor").over(w))
#   out.write.mode("overwrite").parquet("gs://<bucket>/silver/sgs_rolling/")


def main() -> None:
    raise NotImplementedError("silver_rolling_stats: implementar na Fase 2")


if __name__ == "__main__":
    main()
