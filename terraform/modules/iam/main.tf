resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "ledgerops-github"
  display_name              = "LedgerOps GitHub Actions"
  project                   = var.project_id
}

resource "google_service_account" "github_actions" {
  account_id   = "ledgerops-github"
  display_name = "LedgerOps GitHub Actions"
  project      = var.project_id
}
