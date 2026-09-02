variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "ledgerops"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "northamerica-northeast1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "northamerica-northeast1-a"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}
