from fastapi import FastAPI
from app.database import engine
from app.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LedgerOps Transaction Service",
    version="1.0.0"
)


@app.get("/health")
def health():
    return {
        "service": "transaction-service",
        "status": "healthy"
    }


@app.get("/transactions")
def transactions():
    return {
        "message": "Transaction service is running"
    }
