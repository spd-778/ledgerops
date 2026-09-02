from decimal import Decimal

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(
    title="LedgerOps Fraud Service",
    version="1.0.0",
)


class FraudCheckRequest(BaseModel):
    transaction_id: str
    from_account: str
    to_account: str
    currency: str
    amount: Decimal = Field(gt=0)


class FraudCheckResponse(BaseModel):
    transaction_id: str
    decision: str
    risk_score: int
    reason: str


@app.get("/health")
def health():
    return {
        "service": "fraud-service",
        "status": "healthy",
    }


@app.post(
    "/fraud/check",
    response_model=FraudCheckResponse,
)
def fraud_check(request: FraudCheckRequest):
    amount = request.amount

    risk_score = 0
    reasons = []

    if amount >= Decimal("10000"):
        risk_score = 100
        reasons.append("transaction exceeds high-risk threshold")
    elif amount >= Decimal("5000"):
        risk_score = 70
        reasons.append("large transaction")
    elif amount >= Decimal("2000"):
        risk_score = 40
        reasons.append("elevated transaction amount")

    if risk_score >= 70:
        decision = "REJECTED"
    elif risk_score >= 40:
        decision = "REVIEW"
    else:
        decision = "APPROVED"

    reason = (
        ", ".join(reasons)
        if reasons
        else "transaction passed fraud rules"
    )

    return {
        "transaction_id": request.transaction_id,
        "decision": decision,
        "risk_score": risk_score,
        "reason": reason,
    }
