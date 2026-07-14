terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Bucket do lakehouse (Bronze Parquet). Lifecycle enxuto p/ free tier.
resource "google_storage_bucket" "lake" {
  name                        = var.bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true

  lifecycle_rule {
    condition { age = 365 }
    action { type = "Delete" }
  }
}

# Datasets Medallion
resource "google_bigquery_dataset" "bronze" {
  dataset_id = "bronze"
  location   = var.region
}

resource "google_bigquery_dataset" "silver" {
  dataset_id = "silver"
  location   = var.region
}

resource "google_bigquery_dataset" "gold" {
  dataset_id = "gold"
  location   = var.region
}

# TODO(Fase 1+): BigLake external tables (bronze), Cloud Run Jobs,
# Cloud Workflows + Scheduler, Dataform repo/release config.
