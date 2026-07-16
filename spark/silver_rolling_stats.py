"""Silver pesado em PySpark — estatísticas móveis das séries do SGS (BACEN).

Lê o Bronze (Parquet no GCS), calcula médias/desvios móveis por série (janelas de 3/6/12
observações) e grava Parquet, que o Dataform materializa como tabela Silver
`silver.sgs_rolling_stats`.

Roda em Databricks Community Edition ou Dataproc Serverless. Caminhos por env var para
funcionar tanto em nuvem (gs://) quanto local (para teste):

    BRONZE_PATH=gs://bucket/bronze/bacen_sgs/       (entrada)
    SILVER_SPARK_PATH=gs://bucket/silver_spark/sgs_rolling/  (saída)
"""

from __future__ import annotations

import os

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

JANELAS = (3, 6, 12)


def transform(df: DataFrame) -> DataFrame:
    """Tipagem + médias móveis (3/6/12) e desvio móvel (12) por série, ordenado por data."""
    df = df.withColumn("data", F.to_date("data", "dd/MM/yyyy")).withColumn(
        "valor", F.col("valor").cast("double")
    )
    w = Window.partitionBy("serie").orderBy("data")
    for n in JANELAS:
        df = df.withColumn(
            f"media_movel_{n}", F.avg("valor").over(w.rowsBetween(-(n - 1), 0))
        )
    df = df.withColumn("desvio_movel_12", F.stddev("valor").over(w.rowsBetween(-11, 0)))
    return df.select(
        "codigo", "serie", "data", "valor", "media_movel_3", "media_movel_6",
        "media_movel_12", "desvio_movel_12",
    )


def main() -> None:
    bronze_path = os.environ["BRONZE_PATH"]
    output_path = os.environ["SILVER_SPARK_PATH"]

    spark = SparkSession.builder.appName("panorama-br-rolling-stats").getOrCreate()
    df = spark.read.parquet(bronze_path)
    out = transform(df)
    out.write.mode("overwrite").parquet(output_path)
    print(f"[silver_rolling_stats] OK — {out.count()} linhas em {output_path}")
    spark.stop()


if __name__ == "__main__":
    main()
