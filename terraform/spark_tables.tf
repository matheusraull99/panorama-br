# Tabela externa da saída do job PySpark (spark/silver_rolling_stats.py).
# Parquet já tipado; sem particionamento Hive (uma escrita overwrite por run).

resource "google_bigquery_table" "sgs_rolling" {
  dataset_id          = google_bigquery_dataset.silver_spark.dataset_id
  table_id            = "sgs_rolling"
  deletion_protection = false

  external_data_configuration {
    autodetect    = true
    source_format = "PARQUET"
    source_uris   = ["gs://${var.bucket_name}/silver_spark/sgs_rolling/*"]
  }
}
