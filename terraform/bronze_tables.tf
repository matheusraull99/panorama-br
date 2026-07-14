# Tabelas Bronze — externas (BigLake) sobre Parquet particionado (Hive) no GCS.
# O Dataform lê estas tabelas via ${ref("bronze", "...")}.

resource "google_bigquery_table" "bacen_sgs" {
  dataset_id          = google_bigquery_dataset.bronze.dataset_id
  table_id            = "bacen_sgs"
  deletion_protection = false

  external_data_configuration {
    autodetect    = true
    source_format = "PARQUET"
    source_uris   = ["gs://${var.bucket_name}/bronze/bacen_sgs/*"]

    hive_partitioning_options {
      mode              = "AUTO"
      source_uri_prefix = "gs://${var.bucket_name}/bronze/bacen_sgs/"
    }
  }
}

resource "google_bigquery_table" "ibge_sidra" {
  dataset_id          = google_bigquery_dataset.bronze.dataset_id
  table_id            = "ibge_sidra"
  deletion_protection = false

  external_data_configuration {
    autodetect    = true
    source_format = "PARQUET"
    source_uris   = ["gs://${var.bucket_name}/bronze/ibge_sidra/*"]

    hive_partitioning_options {
      mode              = "AUTO"
      source_uri_prefix = "gs://${var.bucket_name}/bronze/ibge_sidra/"
    }
  }
}
