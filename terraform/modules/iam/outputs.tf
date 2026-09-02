output "workload_identity_pool_name" {
  value = google_iam_workload_identity_pool.github.name
}

output "github_service_account" {
  value = google_service_account.github_actions.email
}
