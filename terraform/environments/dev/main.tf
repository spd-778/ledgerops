module "network" {
  source = "../../modules/network"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment
}

module "artifact_registry" {
  source = "../../modules/artifact-registry"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment
}

module "iam" {
  source = "../../modules/iam"

  project_id  = var.project_id
  environment = var.environment
}

module "gke" {
  source = "../../modules/gke"

  project_id        = var.project_id
  region            = var.region
  environment       = var.environment
  network_name      = module.network.network_name
  subnet_name       = module.network.subnet_name
  workload_identity = module.iam.workload_identity_pool_name
}
