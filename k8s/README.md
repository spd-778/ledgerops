# LedgerOps Kubernetes

Kubernetes manifests for the LedgerOps banking transaction platform.

## Services

- PostgreSQL
- Account Service
- Transaction Service
- Fraud Service

## Reliability

- Multiple replicas for application services
- Readiness probes
- Liveness probes
- CPU and memory requests
- CPU and memory limits
- Persistent PostgreSQL storage

## Security

- Secrets separated from application configuration
- Kubernetes namespace isolation
- No privileged application containers

## Deployment

Apply the manifests with:

kubectl apply -k k8s/

Check workloads:

kubectl get pods -n ledgerops
kubectl get services -n ledgerops
