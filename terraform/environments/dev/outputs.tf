output "network_name" {
  value = module.network.network_name
}

output "subnet_name" {
  value = module.network.subnet_name
}

output "artifact_registry_repository" {
  value = module.artifact_registry.repository_name
}

output "workload_identity_pool" {
  value = module.iam.workload_identity_pool_name
}

output "gke_cluster_name" {
  value = module.gke.cluster_name
}
