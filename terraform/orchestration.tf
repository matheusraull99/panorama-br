# Orquestração: Cloud Workflow (pipeline diário) + Scheduler + SA com IAM mínimo.

resource "google_service_account" "workflow" {
  account_id   = "panorama-workflow"
  display_name = "Panorama BR — orquestrador"
}

resource "google_project_iam_member" "workflow_run_invoker" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.workflow.email}"
}

resource "google_project_iam_member" "workflow_dataform" {
  project = var.project_id
  role    = "roles/dataform.editor"
  member  = "serviceAccount:${google_service_account.workflow.email}"
}

resource "google_project_iam_member" "workflow_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.workflow.email}"
}

resource "google_workflows_workflow" "pipeline" {
  name            = "panorama-pipeline"
  region          = var.region
  service_account = google_service_account.workflow.email

  source_contents = templatefile("${path.module}/../workflows/pipeline.yaml", {
    project_id = var.project_id
    region     = var.region
  })
}

resource "google_service_account" "scheduler" {
  account_id   = "panorama-scheduler"
  display_name = "Panorama BR — scheduler"
}

resource "google_project_iam_member" "scheduler_workflow_invoker" {
  project = var.project_id
  role    = "roles/workflows.invoker"
  member  = "serviceAccount:${google_service_account.scheduler.email}"
}

# Diário às 07:00 BRT (dados do BACEN/IBGE são D-1; sem ganho em rodar mais cedo).
resource "google_cloud_scheduler_job" "daily" {
  name      = "panorama-pipeline-daily"
  region    = var.region
  schedule  = "0 7 * * *"
  time_zone = "America/Sao_Paulo"

  http_target {
    http_method = "POST"
    uri         = "https://workflowexecutions.googleapis.com/v1/${google_workflows_workflow.pipeline.id}/executions"

    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }
}
