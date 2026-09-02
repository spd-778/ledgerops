# LedgerOps

## Secure Banking Transaction Pipeline — DevOps / SRE Project

LedgerOps is a production-style financial transaction platform designed to demonstrate practical **DevOps, SRE, cloud, Kubernetes, CI/CD, security, observability, and financial transaction-processing concepts**.

The platform simulates a banking transaction workflow using independently deployable microservices for:

- Account management
- Transaction processing
- Fraud detection
- Transaction audit history
- PostgreSQL persistence
- Kubernetes orchestration
- Prometheus monitoring
- Grafana dashboards
- Automated CI/CD
- Container security scanning
- Infrastructure as Code

The project focuses on **reliability, transaction integrity, security, automation, and operational engineering** rather than simply deploying containers.

---

## Architecture

```text
                                  Client
                                    |
                                    v
                         +----------------------+
                         | Transaction Service  |
                         |       :8002          |
                         +----------+-----------+
                                    |
                    +---------------+---------------+
                    |                               |
                    v                               v
          +-------------------+            +-------------------+
          |   Fraud Service   |            |    PostgreSQL     |
          |       :8003       |            |       :5432       |
          +-------------------+            +---------+---------+
                                                    |
                                          +---------+---------+
                                          |  Account Service  |
                                          |       :8001       |
                                          +-------------------+

                         Observability
                              |
                +-------------+-------------+
                |                           |
                v                           v
        +---------------+           +---------------+
        |  Prometheus   |---------->|    Grafana    |
        |     :9090     |           |     :3000     |
        +---------------+           +---------------+
                |
                +---- HTTP metrics
                +---- Transaction metrics
                +---- Fraud metrics
                +---- Error rates
                +---- Latency
                +---- Availability
                +---- Alerts
```

---

## Core Transaction Flow

A financial transaction follows a controlled workflow:

```text
Client
  |
  v
Transaction Service
  |
  +--> Validate request
  |
  +--> Check idempotency
  |
  +--> Lock source/destination accounts
  |
  +--> Fraud Service
  |
  +---- REJECTED --> Record fraud rejection audit
  |
  +---- APPROVED
          |
          v
      Create PENDING transaction
          |
          v
      Update account balances
          |
          v
      Mark COMPLETED
          |
          v
      Create audit events
          |
          v
      Commit database transaction
```

The design prioritizes:

- Transaction integrity
- Atomic balance updates
- Idempotency
- Fraud controls
- Auditability
- Failure recovery
- Operational visibility

---

# Technology Stack

## Application

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Psycopg2
- Pydantic
- Uvicorn
- Pytest
- Requests

## DevOps

- Git
- GitHub
- Docker
- Docker Compose
- GitHub Actions
- GitHub Container Registry (GHCR)
- Trivy

## Kubernetes

- Kubernetes
- Docker Desktop Kubernetes
- Deployments
- Services
- ConfigMaps
- Secrets
- PersistentVolumeClaims
- Readiness probes
- Liveness probes
- Horizontal Pod Autoscaling
- PodDisruptionBudgets
- NetworkPolicies

## Observability

- Prometheus
- Grafana
- Prometheus recording rules
- Prometheus alert rules
- Application metrics
- HTTP request metrics
- Request latency metrics
- Fraud decision metrics

## Cloud / Infrastructure

- Google Cloud Platform
- Terraform
- Google Artifact Registry
- Google Kubernetes Engine
- Google IAM
- Workload Identity Federation

---

# Services

| Service | Port | Purpose |
|---|---:|---|
| Account Service | 8001 | Account creation, lookup and balance management |
| Transaction Service | 8002 | Atomic transaction processing |
| Fraud Service | 8003 | Fraud evaluation and risk decisions |
| PostgreSQL | 5432 | Persistent relational database |
| Prometheus | 9090 | Metrics collection and alerting |
| Grafana | 3000 | SRE dashboards and visualization |

---

# Account Service

The Account Service manages customer bank accounts and balances.

## Responsibilities

- Account creation
- Account lookup
- Balance retrieval
- Account status validation
- Currency validation
- Persistent account storage

## Health Check

```http
GET /health
```

Example response:

```json
{
  "service": "account-service",
  "status": "healthy"
}
```

## Create Account

```http
POST /accounts
```

Example request:

```json
{
  "customer_id": "CUS-1002",
  "currency": "CAD",
  "initial_balance": 7500
}
```

## Get Account

```http
GET /accounts/{account_id}
```

Example:

```bash
curl http://127.0.0.1:8001/accounts/ACC-C8E952EE
```

## Get Account Balance

```http
GET /accounts/{account_id}/balance
```

Example:

```bash
curl http://127.0.0.1:8001/accounts/ACC-C8E952EE/balance
```

---

# Transaction Service

The Transaction Service is the core financial processing component.

## Responsibilities

- Transaction validation
- Account validation
- Balance validation
- Atomic transfers
- Fraud integration
- Idempotency
- Transaction persistence
- Audit trail generation
- Transaction reversal support

## Transaction Model

| Field | Description |
|---|---|
| id | Internal database identifier |
| transaction_id | Unique transaction identifier |
| from_account | Source account |
| to_account | Destination account |
| currency | Transaction currency |
| amount | Transaction amount |
| status | Current transaction status |
| created_at | Transaction creation timestamp |

## Transaction States

```text
PENDING
COMPLETED
REVERSED
```

---

# Atomic Financial Transfers

The Transaction Service uses database transactions and row-level locking to protect financial consistency.

The source and destination accounts are locked before balances are modified.

Conceptually:

```text
BEGIN DATABASE TRANSACTION

Lock source account
Lock destination account

Validate:
    source account
    destination account
    account status
    currency
    sufficient funds
    source != destination

Run fraud check

Create transaction
Update source balance
Update destination balance
Mark transaction COMPLETED
Create audit events

COMMIT
```

If processing fails, the database transaction is rolled back.

This prevents partial balance updates and protects ledger consistency.

---

# Idempotency

LedgerOps implements idempotency keys to prevent duplicate financial transactions when clients retry requests.

Example:

```http
Idempotency-Key: FINAL-TRANSFER-001
```

If the same idempotency key is submitted again for the same transaction request, the existing transaction is returned rather than creating a duplicate transfer.

This protects against duplicate transactions caused by:

- Client retries
- Network failures
- Request timeouts
- Duplicate submissions

Conflicting reuse of an idempotency key is rejected.

---

# Fraud Service

The Fraud Service evaluates transactions before balances are modified.

## Fraud Rules

| Transaction Amount | Decision | Risk Score |
|---:|---|---:|
| < $2,000 | APPROVED | 0 |
| $2,000–$4,999.99 | REVIEW | 40 |
| $5,000–$9,999.99 | REJECTED | 70 |
| >= $10,000 | REJECTED | 100 |

Example:

```text
Transaction Amount: $6,000
Decision:            REJECTED
Risk Score:          70
Reason:              large transaction
```

Rejected transactions do not update account balances.

---

# Fraud Validation Example

A rejected transaction can be tested through the Transaction Service.

```bash
curl -X POST http://127.0.0.1:8002/transactions \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: FINAL-FRAUD-E2E-001" \
  -d '{
    "from_account": "ACC-C8E952EE",
    "to_account": "ACC-8853F2E7",
    "currency": "CAD",
    "amount": 6000
  }'
```

Expected behavior:

```text
HTTP 403
Transaction rejected
No transaction record created
Account balances remain unchanged
Fraud rejection recorded in audit history
```

This demonstrates that fraud validation occurs before the financial ledger is modified.

---

# Audit Trail

LedgerOps maintains an audit history for transaction processing.

A successful transaction generates events such as:

```text
TRANSACTION_CREATED
        |
        v
FRAUD_CHECK
        |
        v
TRANSACTION_COMPLETED
```

Example:

```text
TRANSACTION_CREATED     | PENDING    | transaction-service
FRAUD_CHECK             | APPROVED   | fraud-service
TRANSACTION_COMPLETED   | COMPLETED  | transaction-service
```

Rejected transactions generate fraud audit events:

```text
FRAUD_CHECK | REJECTED | fraud-service
```

The audit history provides traceability for financial operations and incident investigation.

## Audit Endpoint

```http
GET /audit/transactions/{transaction_id}
```

Example:

```bash
curl http://127.0.0.1:8002/audit/transactions/TXN-CFA01BF14379
```

The endpoint returns:

- Transaction existence
- Transaction status
- Audit event IDs
- Event types
- Event status
- Actor
- Reason
- Timestamp

---

# Transaction Reversal

LedgerOps supports controlled transaction reversal for correction and recovery scenarios.

Example lifecycle:

```text
PENDING
   |
   v
COMPLETED
   |
   v
REVERSED
```

The original transaction remains available for traceability.

A reversal is represented as a new state and corresponding audit event rather than silently deleting the original financial record.

---

# PostgreSQL

PostgreSQL is the primary relational database.

```text
Database: ledgerops
User:     ledgerops
Port:     5432
```

SQLAlchemy provides ORM functionality and Psycopg2 provides PostgreSQL connectivity.

The database contains persistent data for:

- Accounts
- Transactions
- Audit events

PostgreSQL data is persisted using Docker volumes during local development.

Database volumes should not be deleted during normal troubleshooting.

---

# Docker Compose

Docker Compose is used for local PostgreSQL development.

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Check running containers:

```bash
docker ps
```

Expected container:

```text
ledgerops-postgres
```

Stop the application stack:

```bash
docker compose down
```

---

# Environment Configuration

The services use environment variables for runtime configuration.

Example:

```bash
export DATABASE_URL="postgresql+psycopg2://ledgerops:ledgerops_dev_password@localhost:5432/ledgerops"
```

Transaction Service also uses:

```bash
export FRAUD_SERVICE_URL="http://127.0.0.1:8003"
```

Configuration is externalized so application code can be promoted across development, testing, Kubernetes, and cloud environments without hard-coding environment-specific values.

Sensitive credentials should never be committed to Git.

---

# Local Development

## Clone Repository

```bash
git clone https://github.com/spd-778/ledgerops.git
cd ledgerops
```

## Start PostgreSQL

```bash
docker compose up -d postgres
```

## Run Account Service

```bash
cd services/account-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg2://ledgerops:ledgerops_dev_password@localhost:5432/ledgerops"
uvicorn app.main:app --reload --port 8001
```

Account Service:

```text
http://127.0.0.1:8001
```

Swagger documentation:

```text
http://127.0.0.1:8001/docs
```

## Run Fraud Service

Open another terminal:

```bash
cd services/fraud-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

Fraud Service:

```text
http://127.0.0.1:8003
```

Swagger documentation:

```text
http://127.0.0.1:8003/docs
```

## Run Transaction Service

Open another terminal:

```bash
cd services/transaction-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg2://ledgerops:ledgerops_dev_password@localhost:5432/ledgerops"
export FRAUD_SERVICE_URL="http://127.0.0.1:8003"
uvicorn app.main:app --reload --port 8002
```

Transaction Service:

```text
http://127.0.0.1:8002
```

Swagger documentation:

```text
http://127.0.0.1:8002/docs
```

---

# API Testing

## Account Health

```bash
curl http://127.0.0.1:8001/health
```

Expected:

```json
{
  "service": "account-service",
  "status": "healthy"
}
```

## Transaction Health

```bash
curl http://127.0.0.1:8002/health
```

Expected:

```json
{
  "service": "transaction-service",
  "status": "healthy"
}
```

## Fraud Health

```bash
curl http://127.0.0.1:8003/health
```

Expected:

```json
{
  "service": "fraud-service",
  "status": "healthy"
}
```

## Create Account

```bash
curl -X POST http://127.0.0.1:8001/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUS-1002",
    "currency": "CAD",
    "initial_balance": 7500
  }'
```

## Get Account

```bash
curl http://127.0.0.1:8001/accounts/{account_id}
```

## Get Balance

```bash
curl http://127.0.0.1:8001/accounts/{account_id}/balance
```

## Create Transaction

```bash
curl -X POST http://127.0.0.1:8002/transactions \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: DEMO-TRANSFER-001" \
  -d '{
    "from_account": "ACC-C8E952EE",
    "to_account": "ACC-8853F2E7",
    "currency": "CAD",
    "amount": 100
  }'
```

## Get Transaction Audit

```bash
curl http://127.0.0.1:8002/audit/transactions/{transaction_id}
```

---

# Testing

Pytest is used for automated application testing.

Testing covers:

- API behavior
- Health endpoints
- Account creation
- Account retrieval
- Balance retrieval
- Transaction validation
- Transaction creation
- Fraud decisions
- Fraud rejection
- Database operations
- Error handling
- Failure scenarios

Recent verified test results:

```text
Transaction Service: 5 passed
Fraud Service:       4 passed
```

The test suites are also executed automatically through GitHub Actions CI.

---

# CI/CD Pipeline

LedgerOps uses GitHub Actions for automated CI/CD.

The current pipeline performs:

```text
Developer
    |
    | git push
    v
GitHub Repository
    |
    v
GitHub Actions
    |
    +-- Checkout source
    |
    +-- Install dependencies
    |
    +-- Run Transaction Service tests
    |
    +-- Run Fraud Service tests
    |
    +-- Build Account Service image
    |
    +-- Build Transaction Service image
    |
    +-- Build Fraud Service image
    |
    +-- Trivy vulnerability scanning
    |
    +-- Tag container images
    |
    +-- Publish images to GHCR
    |
    v
GitHub Container Registry
```

The CI/CD workflow has been successfully executed with all test, build, scan, and publishing jobs passing.

---

# GitHub Container Registry

Container images are published to GitHub Container Registry.

Images:

```text
ghcr.io/spd-778/ledgerops-account-service
ghcr.io/spd-778/ledgerops-transaction-service
ghcr.io/spd-778/ledgerops-fraud-service
```

Images use both mutable and immutable tags.

Example:

```text
latest
sha-<commit>
```

The Git SHA tag provides an immutable reference to the exact source revision used to build an image.

This improves:

- Deployment traceability
- Release reproducibility
- Rollback capability
- Version control

---

# Container Security

Trivy is integrated into the GitHub Actions pipeline.

The container images are scanned for known vulnerabilities before publishing.

The security gate checks for:

```text
CRITICAL
HIGH
```

with unfixed vulnerabilities ignored.

This provides an automated container-security control within the CI/CD lifecycle.

---

# Kubernetes

LedgerOps is deployed to Kubernetes using declarative manifests.

Local environment:

```text
Docker Desktop Kubernetes
```

Namespace:

```text
ledgerops
```

Application deployments:

```text
account-service
transaction-service
fraud-service
postgres
prometheus
grafana
```

---

# Kubernetes Workload Configuration

Application replicas:

```text
Account Service       2
Transaction Service   2
Fraud Service         2
```

Each service is exposed internally through Kubernetes ClusterIP Services.

Kubernetes configuration includes:

- Deployments
- Services
- ConfigMaps
- Secrets
- Persistent storage
- Readiness probes
- Liveness probes
- Resource configuration
- Horizontal Pod Autoscaling
- PodDisruptionBudgets
- NetworkPolicies

---

# Kubernetes Self-Healing

LedgerOps includes an actual Kubernetes failure-recovery test.

A Transaction Service pod was intentionally deleted during testing.

Before failure:

```text
transaction-service replicas: 2/2
```

One pod was deleted.

Kubernetes automatically created a replacement pod.

Example:

```text
Deleted:
transaction-service-69d756bcf9-9zqzt

Replacement:
transaction-service-69d756bcf9-s8bbj
```

Final state:

```text
Transaction Service: 2/2
Health endpoint:     HTTP 200
Prometheus target:   UP
```

This demonstrates Kubernetes Deployment-based self-healing.

---

# PodDisruptionBudgets

PodDisruptionBudgets are configured for:

```text
account-service
transaction-service
fraud-service
```

Configuration:

```text
minAvailable: 1
```

This protects availability during supported voluntary disruption scenarios.

---

# Horizontal Pod Autoscaling

HPA is configured for:

```text
transaction-service
fraud-service
```

Configuration:

```text
Minimum replicas: 2
Maximum replicas: 5
CPU target:       70%
```

The HPA resources are successfully configured.

The local Docker Desktop Kubernetes environment did not provide an available metrics-server, so CPU utilization appeared as:

```text
<unknown>/70%
```

Therefore, actual CPU-driven autoscaling was not claimed as a locally demonstrated test.

---

# NetworkPolicies

LedgerOps uses Kubernetes NetworkPolicies to restrict unnecessary service-to-service communication.

Transaction Service can communicate with:

```text
PostgreSQL
Fraud Service
DNS
Prometheus
```

Fraud Service accepts traffic from:

```text
Transaction Service
Prometheus
```

Account Service accepts required application and monitoring traffic.

PostgreSQL accepts database traffic from the required application workload.

This provides a basic zero-trust-style east-west network control within the Kubernetes cluster.

---

# Prometheus

Prometheus collects application metrics from the LedgerOps services.

Current metrics include:

```text
ledgerops_http_requests_total
ledgerops_http_request_duration_seconds
ledgerops_fraud_checks_total
```

Prometheus records operational indicators including:

- Transaction request rate
- Transaction error rate
- Fraud rejection rate
- Fraud check rate
- Transaction p95 latency
- Transaction success ratio
- Fraud rejection ratio

Verified Prometheus targets:

```text
transaction-service => UP
fraud-service        => UP
prometheus           => UP
```

---

# Grafana

Grafana provides the LedgerOps SRE dashboard.

Dashboard:

```text
LedgerOps SRE Dashboard
```

Dashboard panels include:

- Transaction request rate
- Transaction success ratio
- Transaction error rate
- Transaction p95 latency
- Fraud check rate
- Fraud rejection ratio
- Service availability
- Active alerts

Grafana is automatically configured with Prometheus as its datasource.

Grafana health was successfully verified.

---

# SRE Alerting

Prometheus alert rules are configured for:

```text
Transaction Service Down
Fraud Service Down
High Transaction Error Rate
High Transaction Latency
High Fraud Rejection Rate
```

Recording rules calculate operational indicators including:

```text
Transaction request rate
Transaction error rate
Fraud rejection rate
Fraud check rate
Transaction p95 latency
Transaction success ratio
Fraud rejection ratio
```

---

# SLI / SLO Strategy

LedgerOps follows an SRE-oriented reliability model.

## Availability SLI

```text
Successful Requests / Total Requests
```

Target:

```text
99.9% availability
```

## Latency SLI

Transaction API latency is monitored using Prometheus histograms.

Example objective:

```text
99% of requests complete within 500ms
```

## Error Rate SLI

```text
Failed Requests / Total Requests
```

Example objective:

```text
Error Rate < 1%
```

---

# Error Budget

For a 99.9% monthly availability SLO:

```text
Allowed downtime ≈ 43.2 minutes/month
```

The error budget provides a framework for balancing:

```text
Reliability
     |
     +---- Change velocity
     |
     +---- Release risk
     |
     +---- Operational stability
```

---

# Incident Management

LedgerOps includes SRE-style incident-management documentation.

Severity levels:

```text
SEV-1
Critical transaction functionality or financial data integrity issue.

SEV-2
Major transaction or fraud-processing degradation.

SEV-3
Limited degradation with a workaround available.
```

Incident lifecycle:

```text
Alert
  |
  v
Detection
  |
  v
Triage
  |
  v
Mitigation
  |
  v
Recovery
  |
  v
Root Cause Analysis
  |
  v
Postmortem
  |
  v
Preventive Improvements
```

Operational documentation is available under:

```text
sre/
├── incident-response.md
├── reliability-testing.md
└── runbook.md
```

---

# Reliability Testing

LedgerOps includes controlled reliability testing rather than only functional testing.

## Service Failure Recovery

```text
Delete Transaction Service Pod
          |
          v
Kubernetes detects replica deficit
          |
          v
Replacement pod created
          |
          v
Readiness restored
          |
          v
Deployment returns to 2/2
          |
          v
Prometheus target remains UP
```

## Fraud Failure Testing

```text
Large transaction
       |
       v
Fraud Service
       |
       v
REJECTED
       |
       v
HTTP 403
       |
       v
No transaction record
       |
       v
Balances unchanged
       |
       v
Audit event recorded
```

These tests demonstrate both application-level and infrastructure-level reliability behavior.

---

# Infrastructure as Code

Terraform is used to define the target GCP infrastructure.

Project structure:

```text
terraform/
├── modules/
│   ├── network/
│   ├── gke/
│   ├── artifact-registry/
│   └── iam/
│
└── environments/
    └── dev/
```

Terraform modules define infrastructure for:

- VPC
- Subnetwork
- GKE cluster
- GKE node pool
- Artifact Registry
- Workload Identity
- GitHub Actions service account
- IAM configuration

Terraform has been validated with:

```bash
terraform init
terraform validate
terraform plan
```

The development plan contains infrastructure resources for the target GCP environment.

Actual GCP infrastructure deployment is currently not performed because the development GCP project does not have active billing.

---

# Workload Identity Federation

The target GCP CI/CD architecture uses GitHub Actions with Workload Identity Federation rather than long-lived service-account keys.

Conceptually:

```text
GitHub Actions
      |
      v
OIDC Identity Token
      |
      v
Google Workload Identity
      |
      v
Short-lived GCP Credentials
      |
      v
GCP Resources
```

This avoids storing permanent Google Cloud service-account credentials in GitHub.

---

# Target GCP Architecture

The target cloud deployment architecture is:

```text
                           GitHub
                              |
                              v
                       GitHub Actions
                              |
                              v
                             GHCR
                              |
                              v
                     Google Cloud Platform
                              |
                       Workload Identity
                              |
                              v
                            GKE
                              |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
   Account Service     Transaction Service    Fraud Service
          |                   |                   |
          +-------------------+-------------------+
                              |
                              v
                         PostgreSQL
                              |
                              v
                   Monitoring / Logging
```

Planned production improvements include:

- GKE
- Cloud networking
- IAM
- Artifact Registry
- Secret management
- Cloud monitoring
- Cloud logging
- Autoscaling
- Production ingress
- TLS
- Automated deployment

The infrastructure is currently **Terraform plan-ready**.

---

# Project Structure

```text
ledgerops/
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml
│
├── services/
│   ├── account-service/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── main.py
│   │   │   └── models.py
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   └── test_accounts.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── transaction-service/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── main.py
│   │   │   └── models.py
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── fraud-service/
│       ├── app/
│       │   ├── __init__.py
│       │   └── main.py
│       ├── tests/
│       ├── requirements.txt
│       └── Dockerfile
│
├── k8s/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── postgres.yaml
│   ├── account-service.yaml
│   ├── transaction-service.yaml
│   ├── fraud-service.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   ├── network-policy.yaml
│   ├── kustomization.yaml
│   │
│   └── observability/
│       ├── prometheus.yaml
│       ├── prometheus-rules.yaml
│       ├── prometheus-config.yaml
│       │
│       └── grafana/
│           ├── grafana.yaml
│           ├── config.yaml
│           ├── dashboard-provider.yaml
│           └── dashboard.json
│
├── sre/
│   ├── incident-response.md
│   ├── reliability-testing.md
│   └── runbook.md
│
├── terraform/
│   ├── modules/
│   │   ├── network/
│   │   ├── gke/
│   │   ├── artifact-registry/
│   │   └── iam/
│   │
│   └── environments/
│       └── dev/
│           ├── main.tf
│           ├── variables.tf
│           ├── outputs.tf
│           ├── providers.tf
│           └── terraform.tfvars.example
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

# Security

Security is incorporated throughout the development lifecycle.

## Implemented Security Controls

- Environment-based configuration
- Credentials excluded from source control
- Kubernetes Secrets
- GitHub Actions OIDC / Workload Identity design
- Container image vulnerability scanning
- Trivy security scanning
- Kubernetes NetworkPolicies
- Least-privilege-oriented IAM design
- Immutable container image SHA tags

## Additional Production Controls

For a production deployment, the following would be added:

- HTTPS/TLS
- API authentication
- Authorization
- External secret management
- Database encryption
- Key management
- Centralized security logging
- Dependency scanning
- Runtime security monitoring
- WAF / ingress protection

---

# Observability Model

LedgerOps follows the three pillars of observability:

```text
                 Observability
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
        Logs       Metrics      Traces
          |           |           |
          v           v           v
       Events     Prometheus    Future
                    |
                    v
                 Grafana
```

Current implementation focuses primarily on:

- Metrics
- Dashboards
- Alerts
- Application logging
- Health checks
- Audit events

Distributed tracing is identified as a future production enhancement.

---

# Metrics

Application metrics include:

```text
ledgerops_http_requests_total
ledgerops_http_request_duration_seconds
ledgerops_fraud_checks_total
```

HTTP metrics track:

- HTTP method
- API path
- HTTP status
- Request count
- Request latency

Fraud metrics track:

- Approved checks
- Review decisions
- Rejected checks

These metrics provide the foundation for SLI calculation and SRE alerting.

---

# SRE Dashboard

The Grafana dashboard provides operational visibility into:

```text
Transaction Request Rate
Transaction Success Ratio
Transaction Error Rate
Transaction p95 Latency
Fraud Check Rate
Fraud Rejection Ratio
Service Availability
Active Alerts
```

This allows an operator to move from:

```text
User reports problem
        |
        v
Check dashboard
        |
        v
Identify affected service
        |
        v
Inspect metrics
        |
        v
Inspect logs
        |
        v
Follow runbook
        |
        v
Mitigate incident
```

---

# CI/CD Reliability

The CI/CD pipeline acts as an automated quality gate.

```text
Code Change
    |
    v
Automated Tests
    |
    v
Container Build
    |
    v
Security Scan
    |
    v
Immutable Image
    |
    v
Container Registry
    |
    v
Deployment
    |
    v
Health Verification
```

This reduces the risk of deploying untested or vulnerable application artifacts.

---

# Deployment Strategy

Container images are tagged using the Git commit SHA.

Example:

```text
ledgerops-transaction-service:sha-abc123
```

This enables:

```text
Release A
   |
   v
sha-111111
   |
   v
Release B
   |
   v
sha-222222
```

If Release B introduces a problem, the exact previous image can be identified and redeployed.

This is preferable to relying only on a mutable `latest` tag.

---

# Failure Scenarios

LedgerOps has been designed around common distributed-system failure scenarios.

## Fraud Service Rejection

```text
Transaction
    |
    v
Fraud Service
    |
    v
REJECTED
    |
    +--> HTTP 403
    +--> No transaction persisted
    +--> No balance update
    +--> Audit event recorded
```

## Transaction Service Pod Failure

```text
Pod deleted
    |
    v
Kubernetes Deployment
    |
    v
Replacement pod
    |
    v
Readiness check
    |
    v
2/2 replicas restored
```

## Application Error

```text
Request
   |
   v
Validation / Processing
   |
   v
Exception
   |
   v
Database rollback
   |
   v
No partial ledger update
```

---

# Banking / Financial Engineering Concepts

LedgerOps intentionally incorporates concepts relevant to financial systems engineering.

## Transaction Integrity

Financial transfers are performed inside database transactions.

## Idempotency

Retrying the same request does not create duplicate transfers.

## Atomicity

Source and destination balance updates occur within one database transaction.

## Consistency

Validation prevents invalid account, currency, and balance states.

## Auditability

Transaction lifecycle events are persisted for investigation and traceability.

## Fraud Controls

Transactions are evaluated before balances are changed.

## Reversal

Completed transactions can be moved to a reversed state for controlled correction workflows.

## Reliability

The system is designed to tolerate application pod failure and recover automatically through Kubernetes.

---

# Development Workflow

```text
1. Develop feature
        |
        v
2. Run tests locally
        |
        v
3. Commit changes
        |
        v
4. Push to GitHub
        |
        v
5. GitHub Actions
        |
        v
6. Automated tests
        |
        v
7. Docker build
        |
        v
8. Security scan
        |
        v
9. Push image to GHCR
        |
        v
10. Deploy
        |
        v
11. Health verification
        |
        v
12. Monitor
        |
        v
13. Incident response / rollback if required
```

---

# Validation Results

The project has been validated across multiple layers.

## Application Testing

```text
Transaction Service tests: 5 passed
Fraud Service tests:       4 passed
```

## CI/CD

The GitHub Actions pipeline successfully completed:

```text
Transaction Service tests
Fraud Service tests
Account Service image build
Transaction Service image build
Fraud Service image build
Trivy scans
GHCR publishing
```

## Kubernetes

Verified:

```text
Account Service:       2/2 replicas
Transaction Service:   2/2 replicas
Fraud Service:         2/2 replicas
PostgreSQL:            Running
Prometheus:            Running
Grafana:               Running
```

## Prometheus

Verified targets:

```text
transaction-service => UP
fraud-service        => UP
prometheus           => UP
```

## Grafana

Verified:

```text
Database: OK
Prometheus datasource: configured
LedgerOps dashboard: available
```

## Kubernetes Self-Healing

Verified:

```text
Pod deletion
     |
     v
Replacement pod created
     |
     v
Pod Ready
     |
     v
Deployment restored to 2/2
```

## Fraud End-to-End Validation

Verified:

```text
$6,000 transaction
        |
        v
Fraud rejection
        |
        v
HTTP 403
        |
        v
No transaction record
        |
        v
Balances unchanged
        |
        v
Audit rejection recorded
```

---

# Current Project Status

## Completed

- [x] Git repository
- [x] Account Service
- [x] Transaction Service
- [x] Fraud Service
- [x] PostgreSQL integration
- [x] SQLAlchemy models
- [x] Account creation
- [x] Account lookup
- [x] Balance retrieval
- [x] Transaction creation
- [x] Atomic account transfers
- [x] Database row locking
- [x] Transaction validation
- [x] Balance validation
- [x] Currency validation
- [x] Idempotency
- [x] Fraud validation
- [x] Fraud rejection
- [x] Transaction audit trail
- [x] Transaction reversal
- [x] Dockerfiles
- [x] Docker Compose
- [x] GitHub Actions CI/CD
- [x] Automated testing
- [x] Docker image builds
- [x] Trivy security scanning
- [x] GHCR publishing
- [x] Immutable SHA image tags
- [x] Kubernetes deployments
- [x] Kubernetes Services
- [x] Kubernetes health probes
- [x] Kubernetes Secrets
- [x] Kubernetes ConfigMaps
- [x] Prometheus
- [x] Prometheus recording rules
- [x] Prometheus alert rules
- [x] Grafana
- [x] Grafana SRE dashboard
- [x] HPA configuration
- [x] PodDisruptionBudgets
- [x] Kubernetes NetworkPolicies
- [x] Kubernetes self-healing test
- [x] SLI/SLO definitions
- [x] Error budget definition
- [x] Incident response documentation
- [x] Reliability testing documentation
- [x] SRE runbook
- [x] Terraform modules
- [x] Terraform validation
- [x] Terraform plan
- [x] GCP IAM design
- [x] Workload Identity Federation design

---

# Current Cloud Limitation

The GCP infrastructure is **Terraform plan-ready**, but the project has not been applied to GCP because the development GCP project currently does not have an active billing account.

Therefore, the project intentionally does **not** claim that the GKE production deployment has been completed.

The demonstrated environment is:

```text
Local Development
      |
      v
Docker
      |
      v
Docker Compose

and

Docker Desktop Kubernetes
      |
      +--> Microservices
      +--> PostgreSQL
      +--> Prometheus
      +--> Grafana
      +--> HPA
      +--> PDB
      +--> NetworkPolicies
      +--> Self-healing
```

The Terraform configuration provides the path to the target GCP environment once billing is available.

---

# Roadmap

The core project is complete as a DevOps/SRE portfolio implementation.

Potential future production enhancements include:

- [ ] Deploy Terraform infrastructure to GCP
- [ ] Deploy workloads to GKE
- [ ] Configure production ingress
- [ ] Configure HTTPS/TLS
- [ ] Configure Cloud Load Balancing
- [ ] Configure Google Cloud Monitoring
- [ ] Configure Google Cloud Logging
- [ ] Add managed PostgreSQL
- [ ] Add centralized secrets management
- [ ] Add API authentication
- [ ] Add authorization / RBAC
- [ ] Add distributed tracing
- [ ] Add OpenTelemetry
- [ ] Add dependency vulnerability scanning
- [ ] Add load testing
- [ ] Add chaos testing
- [ ] Add production-grade backup and disaster recovery
- [ ] Add multi-environment Terraform configuration

---

# Key DevOps / SRE Concepts Demonstrated

This project demonstrates practical experience with:

### Software Engineering

- Python
- FastAPI
- REST APIs
- SQLAlchemy
- PostgreSQL
- Microservices
- Automated testing

### DevOps

- Git
- GitHub
- Docker
- Docker Compose
- GitHub Actions
- CI/CD
- GHCR
- Immutable container images
- Automated security scanning

### Kubernetes

- Deployments
- Services
- ConfigMaps
- Secrets
- Health probes
- Replica management
- HPA
- PDB
- NetworkPolicies
- Self-healing

### Cloud

- Google Cloud Platform
- GKE
- Artifact Registry
- IAM
- Workload Identity Federation
- Terraform

### Observability

- Prometheus
- Grafana
- Metrics
- Dashboards
- Recording rules
- Alert rules
- Application logging
- Health checks

### SRE

- SLIs
- SLOs
- Error budgets
- Alerting
- Incident response
- Runbooks
- Reliability testing
- Failure recovery
- Service availability
- Latency monitoring
- Error-rate monitoring

### Financial Systems

- Atomic transactions
- Database locking
- Idempotency
- Fraud detection
- Audit trails
- Transaction lifecycle
- Transaction reversal
- Ledger consistency

---

# Screenshots

## CI/CD Pipeline

<img width="1710" height="1026" alt="LedgerOps CI/CD Pipeline" src="https://github.com/user-attachments/assets/ab268816-e7e8-4b11-9aa8-941327f1fde2" />

## Kubernetes / Observability

<img width="1710" height="1026" alt="LedgerOps Kubernetes and Observability" src="https://github.com/user-attachments/assets/f0cc2baf-4bd7-4903-a266-ceea8da1fde2" />

---

# Project Goal

The goal of LedgerOps is to demonstrate how a financial transaction platform can evolve from application-level services into a production-style operational platform.

The project brings together:

```text
Financial Transaction Processing
              +
        Microservices
              +
           Docker
              +
        Kubernetes
              +
           CI/CD
              +
          Security
              +
       Observability
              +
             SRE
              +
      Infrastructure as Code
              |
              v
    Production-Ready Architecture
```

The emphasis is on building systems that are not only functional, but also:

- Reliable
- Observable
- Secure
- Testable
- Recoverable
- Deployable
- Auditable
- Operationally maintainable

---

# Repository

GitHub:

https://github.com/spd-778/ledgerops

Branch:

```text
master
```

---

# Author

**Prathyusha Danthuluri**

GitHub:

https://github.com/spd-778

---

# License

This project is intended for educational, portfolio, and DevOps/SRE demonstration purposes.


<img width="1710" height="1026" alt="image" src="https://github.com/user-attachments/assets/ab268816-e7e8-4b11-9aa8-941327f1fde2" />
<img width="1710" height="1026" alt="image" src="https://github.com/user-attachments/assets/f0cc2baf-4bd7-4903-a266-ceea8ada1365" />

