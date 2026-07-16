# Artifact Registry + Cloud Run Jobs dos extratores Bronze.

resource "google_artifact_registry_repository" "docker" {
  repository_id = "panorama-br"
  location      = var.region
  format        = "DOCKER"

  cleanup_policies {
    id     = "keep-latest-only"
    action = "DELETE"
    condition {
      older_than = "2592000s" # 30 dias
    }
  }
}

locals {
  image = "${var.region}-docker.pkg.dev/${var.project_id}/panorama-br/extractor:latest"

  bronze_jobs = {
    "brz-bacen-sgs"  = "jobs.bronze.bacen_sgs"
    "brz-ibge-sidra" = "jobs.bronze.ibge_sidra"
  }
}

resource "google_service_account" "jobs" {
  account_id   = "panorama-jobs"
  display_name = "Panorama BR — extratores Bronze"
}

resource "google_storage_bucket_iam_member" "jobs_writer" {
  bucket = google_storage_bucket.lake.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.jobs.email}"
}

resource "google_cloud_run_v2_job" "bronze" {
  for_each = local.bronze_jobs

  name     = each.key
  location = var.region

  template {
    template {
      service_account = google_service_account.jobs.email
      max_retries     = 1

      containers {
        image   = local.image
        command = ["python", "-m", each.value]

        env {
          name  = "BUCKET_NAME"
          value = google_storage_bucket.lake.name
        }
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
      }
    }
  }
}
