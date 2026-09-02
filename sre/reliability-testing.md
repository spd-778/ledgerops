# LedgerOps Reliability Testing

## Kubernetes Self-Healing Test

LedgerOps was tested by intentionally deleting one transaction-service pod.

- Original pod was terminated successfully
- Kubernetes automatically created a replacement pod
- Transaction Service returned to 2/2 replicas
- Health endpoint remained HTTP 200
- Prometheus target remained UP
- PodDisruptionBudget remained configured
- PostgreSQL and persistent data were not deleted

## HPA

Transaction Service and Fraud Service are configured with HPA from 2 to 5 replicas and a 70% CPU target.

Docker Desktop did not expose metrics-server during local verification, so CPU utilization displayed as <unknown>. The HPA resources themselves are configured.

## PDB

Account, Fraud, and Transaction Services use minAvailable: 1.

## NetworkPolicy

NetworkPolicies restrict communication between application services, PostgreSQL, Prometheus, and DNS.
