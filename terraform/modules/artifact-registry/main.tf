resource "google_artifact_registry_repository" "ledgerops" {
  location      = var.region
  repository_id = "ledgerops"
  description   = "LedgerOps container images"
  format        = "DOCKER"
  project       = var.project_id
}
