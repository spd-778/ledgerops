# LedgerOps

LedgerOps is a production-style financial transaction platform designed to demonstrate modern DevOps, SRE, microservices, containerization, CI/CD, database management, monitoring, and cloud deployment practices.

The project simulates a financial ledger platform with independently deployable services for account and transaction management.

## Architecture

```text
                         Client
                           |
                           v
                    +-------------+
                    | API Services|
                    +------+------+
                           |
              +------------+------------+
              |                         |
              v                         v
      +---------------+         +---------------+
      | Account       |         | Transaction   |
      | Service       |         | Service       |
      | Port 8001     |         | Port 8002     |
      +-------+-------+         +-------+-------+
              |                         |
              +------------+------------+
                           |
                           v
                    +-------------+
                    | PostgreSQL  |
                    | Port 5432   |
                    +-------------+
```

## Technology Stack

### Application

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Psycopg2
- Pydantic
- Uvicorn
- Pytest

### DevOps

- Git
- GitHub
- Docker
- Docker Compose
- GitHub Actions
- GitHub Container Registry (GHCR)

### Cloud

- Google Cloud Platform (GCP)
- Containerized services
- Infrastructure as Code
- Cloud-based monitoring and logging

### SRE

- Health checks
- SLIs
- SLOs
- Error budgets
- Monitoring
- Logging
- Observability
- Incident management
- Failure recovery
- CI/CD automation

## Project Structure

```text
ledgerops/
│
├── services/
│   │
│   ├── account-service/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── main.py
│   │   │   └── models.py
│   │   │
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   └── test_accounts.py
│   │   │
│   │   ├── requirements.txt
│   │   └── README.md
│   │
│   └── transaction-service/
│       ├── app/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   ├── main.py
│       │   └── models.py
│       │
│       └── requirements.txt
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Services

| Service | Port | Purpose |
|---|---:|---|
| Account Service | 8001 | Account creation, lookup and balance management |
| Transaction Service | 8002 | Transaction processing and transaction management |
| PostgreSQL | 5432 | Persistent relational database |

## Account Service

The Account Service manages customer bank accounts and account balances.

### Health Check

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

### Create Account

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

Example response:

```json
{
  "account_id": "ACC-C9E952EE",
  "customer_id": "CUS-1002",
  "currency": "CAD",
  "balance": 7500.0,
  "status": "ACTIVE"
}
```

### Get Account

```http
GET /accounts/{account_id}
```

Example:

```bash
curl http://127.0.0.1:8001/accounts/ACC-C9E952EE
```

### Get Account Balance

```http
GET /accounts/{account_id}/balance
```

Example:

```bash
curl http://127.0.0.1:8001/accounts/ACC-C9E952EE/balance
```

Example response:

```json
{
  "account_id": "ACC-C9E952EE",
  "currency": "CAD",
  "balance": 7500.0
}
```

## Transaction Service

The Transaction Service handles transaction-related operations and stores transaction data in PostgreSQL.

### Transaction Model

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

Supported transaction states are planned as:

```text
PENDING
COMPLETED
FAILED
```

### Health Check

```http
GET /health
```

Example response:

```json
{
  "service": "transaction-service",
  "status": "healthy"
}
```

### Transactions Endpoint

```http
GET /transactions
```

Current response:

```json
{
  "message": "Transaction service is running"
}
```

Transaction processing functionality will be expanded as development continues.

## Database

LedgerOps uses PostgreSQL as the primary relational database.

PostgreSQL currently runs inside Docker using Docker Compose.

```text
Database: ledgerops
User: ledgerops
Port: 5432
```

SQLAlchemy is used as the ORM and Psycopg2 is used as the PostgreSQL driver.

The database currently contains an `accounts` table for the Account Service and a `transactions` table for the Transaction Service.

PostgreSQL data is persisted using a Docker volume.

## Docker Compose

PostgreSQL is currently containerized using Docker Compose.

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

Stop the database:

```bash
docker compose down
```

## Environment Configuration

The services use the `DATABASE_URL` environment variable for database configuration.

Example:

```bash
export DATABASE_URL="postgresql+psycopg2://ledgerops:ledgerops_dev_password@localhost:5432/ledgerops"
```

The application reads the configuration using an environment variable rather than hard-coding the production configuration.

Example:

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL")
```

This allows the same application code to be used across development, testing, and production environments.

Sensitive credentials should never be committed to Git.

## Local Development

### Clone Repository

```bash
git clone https://github.com/spd-778/ledgerops.git
cd ledgerops
```

### Start PostgreSQL

```bash
docker compose up -d postgres
```

Verify:

```bash
docker ps
```

### Run Account Service

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

### Run Transaction Service

Open another terminal:

```bash
cd services/transaction-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg2://ledgerops:ledgerops_dev_password@localhost:5432/ledgerops"
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

## API Testing

### Account Service Health

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

### Create Account

```bash
curl -X POST http://127.0.0.1:8001/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUS-1002",
    "currency": "CAD",
    "initial_balance": 7500
  }'
```

### Get Account

```bash
curl http://127.0.0.1:8001/accounts/{account_id}
```

### Get Balance

```bash
curl http://127.0.0.1:8001/accounts/{account_id}/balance
```

### Transaction Service Health

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

### Transactions

```bash
curl http://127.0.0.1:8002/transactions
```

Expected:

```json
{
  "message": "Transaction service is running"
}
```

## Testing

Pytest is used for automated testing.

Run tests:

```bash
pytest
```

Testing will cover:

- API health checks
- Account creation
- Account retrieval
- Balance retrieval
- Transaction creation
- Transaction validation
- Database operations
- Error handling
- Failure scenarios

The goal is to execute automated tests as part of the CI/CD pipeline.

## CI/CD Pipeline

LedgerOps is designed around an automated CI/CD workflow using GitHub Actions.

The target pipeline is:

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
    +-- Checkout Code
    |
    +-- Install Dependencies
    |
    +-- Run Tests
    |
    +-- Lint / Validate
    |
    +-- Build Docker Images
    |
    +-- Security Scan
    |
    +-- Push Images to GHCR
    |
    +-- Deploy to GCP
    |
    +-- Health Check
    |
    +-- Verify Deployment
```

Planned CI/CD capabilities:

- Automated testing
- Docker image builds
- Docker image tagging
- GitHub Container Registry
- Security scanning
- Deployment automation
- Deployment verification
- Health checks
- Rollback strategy

## GitHub Container Registry

Docker images will be published to GitHub Container Registry.

Planned Account Service image:

```text
ghcr.io/spd-778/ledgerops-account-service
```

Planned Transaction Service image:

```text
ghcr.io/spd-778/ledgerops-transaction-service
```

Example image tags:

```text
latest
v1.0.0
sha-abc123
```

## Google Cloud Deployment

The target production environment is Google Cloud Platform.

Planned deployment architecture:

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
                     Google Cloud
                            |
             +--------------+--------------+
             |                             |
             v                             v
      Account Service              Transaction Service
             |                             |
             +--------------+--------------+
                            |
                            v
                       PostgreSQL
                            |
                            v
                  Monitoring / Logging
```

Planned cloud capabilities include:

- Containerized application deployment
- Cloud networking
- IAM
- Secret management
- Monitoring
- Logging
- Health checks
- Autoscaling
- Infrastructure as Code

## SRE & Observability

LedgerOps follows an SRE-oriented approach to reliability.

The reliability strategy focuses on:

```text
Reliability
    |
    +-- Availability
    +-- Latency
    +-- Error Rate
    +-- Throughput
    +-- Resource Utilization

Observability
    |
    +-- Logs
    +-- Metrics
    +-- Traces

SRE
    |
    +-- SLIs
    +-- SLOs
    +-- Error Budgets
    +-- Alerts
    +-- Incident Response
    +-- Postmortems
```

## SLI / SLO Strategy

### Availability

The availability SLI measures the percentage of successful API requests.

```text
SLI = Successful Requests / Total Requests
```

Example target:

```text
99.9% availability
```

### Latency

The latency SLI measures how quickly API requests are completed.

Example objective:

```text
99% of API requests complete within 500ms
```

### Error Rate

The error rate measures the percentage of failed API requests.

```text
Error Rate = Failed Requests / Total Requests
```

Example objective:

```text
Error Rate < 1%
```

## Monitoring Roadmap

Planned monitoring capabilities:

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] API latency monitoring
- [ ] Request rate monitoring
- [ ] Error-rate monitoring
- [ ] Database health monitoring
- [ ] Container health monitoring
- [ ] CPU monitoring
- [ ] Memory monitoring
- [ ] Alerting
- [ ] Centralized logging
- [ ] Distributed tracing

## Incident Management

The project will incorporate SRE-style incident management.

Planned capabilities:

- Incident severity levels
- Alert definitions
- On-call procedures
- Troubleshooting runbooks
- Root cause analysis
- Post-incident reviews
- Preventive actions

Example incident lifecycle:

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

## Security

Security is incorporated throughout the development lifecycle.

Current practices:

- Environment-based configuration
- `.env` files excluded from Git
- Virtual environments excluded from Git
- Credentials excluded from source control

Planned security capabilities:

- [ ] Secret management
- [ ] IAM least privilege
- [ ] Container image scanning
- [ ] Dependency vulnerability scanning
- [ ] Secure CI/CD credentials
- [ ] HTTPS/TLS
- [ ] API authentication
- [ ] Authorization
- [ ] Audit logging

## Microservice Design

LedgerOps uses independently deployable services.

Each service is designed to have:

- Independent application code
- Independent dependencies
- Independent database models
- Independent API endpoints
- Independent tests
- Independent runtime configuration

This allows services to be developed, tested, deployed, and scaled independently.

## Development Workflow

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
10. Deploy to GCP
        |
        v
11. Health check
        |
        v
12. Monitor
```

## Current Status

### Completed

- [x] Git repository initialized
- [x] Account Service created
- [x] Account database model
- [x] PostgreSQL integration
- [x] Account creation API
- [x] Account lookup API
- [x] Account balance API
- [x] PostgreSQL Docker container
- [x] Docker Compose configuration
- [x] Transaction Service scaffold
- [x] Transaction database model
- [x] Transaction PostgreSQL integration
- [x] Transaction health endpoint
- [x] Transaction API endpoint
- [x] Environment-based DATABASE_URL
- [x] Git version control

### In Progress

- [ ] Transaction creation API
- [ ] Account-to-account transfers
- [ ] Transaction validation
- [ ] Balance updates
- [ ] Transaction status management
- [ ] Automated transaction tests
- [ ] Dockerfiles for application services
- [ ] GitHub Actions CI/CD
- [ ] GHCR image publishing
- [ ] Security scanning
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] SLO/SLI implementation
- [ ] Alerting
- [ ] Incident runbooks
- [ ] GCP deployment
- [ ] Infrastructure as Code
- [ ] Production-grade observability

## Roadmap

### Phase 1 — Core Services

- Complete Account Service
- Complete Transaction Service
- Implement transaction creation
- Implement account-to-account transfers
- Add validation
- Add error handling
- Expand automated tests

### Phase 2 — Containerization

- Create service Dockerfiles
- Containerize Account Service
- Containerize Transaction Service
- Update Docker Compose
- Implement container health checks

### Phase 3 — CI/CD

- Create GitHub Actions workflows
- Run automated tests
- Build Docker images
- Scan images
- Push images to GHCR
- Implement deployment automation

### Phase 4 — SRE

- Implement Prometheus metrics
- Create Grafana dashboards
- Define SLIs and SLOs
- Configure alerts
- Create incident runbooks
- Implement structured logging
- Add failure testing

### Phase 5 — Cloud

- Deploy services to GCP
- Configure IAM
- Configure secrets
- Configure networking
- Implement Infrastructure as Code
- Configure monitoring
- Configure production logging
- Implement autoscaling

## Key DevOps / SRE Concepts Demonstrated

This project is intended to demonstrate practical experience with:

- Microservices
- REST APIs
- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Docker
- Docker Compose
- Git
- GitHub
- GitHub Actions
- GHCR
- CI/CD
- Cloud deployment
- Infrastructure as Code
- Observability
- Monitoring
- Logging
- Metrics
- SLIs
- SLOs
- Error budgets
- Incident management
- Reliability engineering
- Security
- Automated testing

## Project Goal

The ultimate goal of LedgerOps is to evolve from a locally running microservice application into a production-style financial platform with:

- Containerized microservices
- Automated CI/CD
- Secure cloud deployment
- Highly available infrastructure
- PostgreSQL persistence
- Automated testing
- Monitoring and observability
- SLO-driven reliability
- Incident management
- Infrastructure as Code
- Security scanning
- Automated deployment and rollback

---

## Author

**Prathyusha Danthuluri**

GitHub: https://github.com/spd-778

## License

This project is intended for educational, portfolio, and DevOps/SRE demonstration purposes.
