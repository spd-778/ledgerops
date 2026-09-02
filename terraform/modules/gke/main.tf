resource "google_container_cluster" "ledgerops" {
  name     = "ledgerops-${var.environment}"
  project  = var.project_id
  location = var.region

  network    = var.network_name
  subnetwork = var.subnet_name

  deletion_protection = false

  remove_default_node_pool = true
  initial_node_count       = 1

  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
}

resource "google_container_node_pool" "primary" {
  name       = "ledgerops-primary"
  project    = var.project_id
  location   = var.region
  cluster    = google_container_cluster.ledgerops.name
  node_count = 1

  node_config {
    machine_type = "e2-small"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}
