from decimal import Decimal
import logging

from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, generate_latest
from pydantic import BaseModel, Field
from starlette.responses import Response


logging.basicConfig(
    level="INFO",
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("ledgerops.fraud-service")


FRAUD_CHECKS_TOTAL = Counter(
    "ledgerops_fraud_checks_total",
    "Total number of fraud checks",
    ["result"],
)


class FraudCheckRequest(BaseModel):
    transaction_id: str
    from_account: str
    to_account: str
    currency: str = "CAD"
    amount: Decimal = Field(gt=0)


app = FastAPI(
    title="LedgerOps Fraud Service",
    version="2.0.0",
)


@app.get("/health")
def health():
    return {
        "service": "fraud-service",
        "status": "healthy",
    }


@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type="text/plain",
    )


def fraud_check(request: FraudCheckRequest):
    amount = request.amount

    if amount >= Decimal("10000"):
        decision = "REJECTED"
        risk_score = 100
        reason = "transaction exceeds high-risk threshold"

    elif amount >= Decimal("5000"):
        decision = "REJECTED"
        risk_score = 70
        reason = "large transaction"

    elif amount >= Decimal("2000"):
        decision = "REVIEW"
        risk_score = 40
        reason = "elevated transaction amount"

    else:
        decision = "APPROVED"
        risk_score = 0
        reason = "transaction passed fraud rules"

    FRAUD_CHECKS_TOTAL.labels(
        result=decision.lower()
    ).inc()

    logger.info(
        "fraud_check transaction_id=%s amount=%s "
        "risk_score=%s decision=%s",
        request.transaction_id,
        amount,
        risk_score,
        decision,
    )

    return {
        "transaction_id": request.transaction_id,
        "decision": decision,
        "risk_score": risk_score,
        "reason": reason,
    }


@app.post("/fraud/check")
def fraud_check_endpoint(request: FraudCheckRequest):
    result = fraud_check(request)

    if result["decision"] == "REJECTED":
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Transaction rejected by fraud service",
                "risk_score": result["risk_score"],
                "reason": result["reason"],
            },
        )

    return result
