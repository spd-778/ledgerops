output "network_name" {
  value = google_compute_network.main.name
}

output "subnet_name" {
  value = google_compute_subnetwork.main.name
}
