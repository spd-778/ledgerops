# LedgerOps Operations Runbook

## Health

curl http://127.0.0.1:8002/health
curl http://127.0.0.1:8003/health

## Kubernetes

kubectl get pods -n ledgerops
kubectl get deployments -n ledgerops
kubectl get pdb -n ledgerops
kubectl get networkpolicy -n ledgerops
kubectl get hpa -n ledgerops

## Prometheus

Expected targets: transaction-service UP, fraud-service UP, prometheus UP.

## Grafana

kubectl port-forward -n ledgerops svc/grafana 3000:3000
curl http://127.0.0.1:3000/api/health

## Self-Healing

kubectl delete pod <pod-name> -n ledgerops
kubectl get pods -n ledgerops
kubectl rollout status deployment/transaction-service -n ledgerops

## Database Safety

Never delete the PostgreSQL persistent volume during normal troubleshooting.
Never use docker compose down -v for LedgerOps database recovery.
