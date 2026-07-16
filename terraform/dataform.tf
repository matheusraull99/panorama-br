# Dataform: repositório ligado ao GitHub + release config + workflow config combinado.

variable "dataform_github_token_secret" {
  description = "Nome do secret (Secret Manager) com o token GitHub p/ o Dataform ler o repo"
  type        = string
  default     = "dataform-github-token"
}

data "google_secret_manager_secret_version" "dataform_token" {
  secret = var.dataform_github_token_secret
}

resource "google_dataform_repository" "panorama" {
  provider = google-beta
  name     = "panorama-br"
  region   = var.region

  git_remote_settings {
    url                                 = "https://github.com/matheusraull99/panorama-br.git"
    default_branch                      = "main"
    authentication_token_secret_version = data.google_secret_manager_secret_version.dataform_token.name
  }
}

resource "google_dataform_repository_release_config" "main" {
  provider   = google-beta
  repository = google_dataform_repository.panorama.name
  region     = var.region
  name       = "main"

  git_commitish = "main"
  cron_schedule = "0 6 * * *" # recompila diariamente antes do pipeline
  time_zone     = "America/Sao_Paulo"
}

# ÚNICO workflow config com Silver + Gold: o Dataform resolve a ordem via ref().
# Configs separados por camada criam race condition (Gold rodando antes do Silver).
resource "google_dataform_repository_workflow_config" "run_all" {
  provider   = google-beta
  repository = google_dataform_repository.panorama.name
  region     = var.region
  name       = "run-all"

  release_config = google_dataform_repository_release_config.main.id

  invocation_config {
    included_tags = ["silver", "gold"]
  }
}
