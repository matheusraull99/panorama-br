variable "project_id" {
  description = "ID do projeto GCP (BigQuery sandbox)"
  type        = string
}

variable "region" {
  description = "Região dos recursos"
  type        = string
  default     = "southamerica-east1"
}

variable "bucket_name" {
  description = "Nome do bucket GCS do lakehouse (globalmente único)"
  type        = string
}
