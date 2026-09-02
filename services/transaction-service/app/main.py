from contextlib import asynccontextmanager
from decimal import Decimal
import logging
import os
from uuid import uuid4

import requests
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import Account, AuditEvent, Base, Transaction


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("ledgerops.transaction-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing transaction service database")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Transaction service shutting down")


app = FastAPI(
    title="LedgerOps Transaction Service",
    version="1.1.0",
    lifespan=lifespan,
)


FRAUD_SERVICE_URL = os.getenv(
    "FRAUD_SERVICE_URL",
    "http://127.0.0.1:8003",
)

FRAUD_TIMEOUT_SECONDS = float(
    os.getenv("FRAUD_TIMEOUT_SECONDS", "3")
)


class TransactionCreate(BaseModel):
    from_account: str
    to_account: str
    currency: str = "CAD"
    amount: Decimal = Field(gt=0)
    idempotency_key: str = Field(
        min_length=1,
        max_length=100,
    )


class TransactionRequestBody(BaseModel):
    from_account: str
    to_account: str
    currency: str = "CAD"
    amount: Decimal = Field(gt=0)
    idempotency_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )


class TransactionResponse(BaseModel):
    transaction_id: str
    idempotency_key: str
    from_account: str
    to_account: str
    currency: str
    amount: Decimal
    status: str

    model_config = ConfigDict(from_attributes=True)


def create_audit_event(
    db: Session,
    transaction_id: str,
    event_type: str,
    event_status: str,
    actor: str,
    reason: str | None = None,
):
    event = AuditEvent(
        transaction_id=transaction_id,
        event_type=event_type,
        event_status=event_status,
        actor=actor,
        reason=reason,
    )

    db.add(event)
    db.flush()

    logger.info(
        "audit_event transaction_id=%s event_type=%s event_status=%s actor=%s",
        transaction_id,
        event_type,
        event_status,
        actor,
    )

    return event


@app.get("/health")
def health():
    return {
        "service": "transaction-service",
        "status": "healthy",
    }


@app.post(
    "/transactions",
    response_model=TransactionResponse,
)
def create_transaction(
    payload: TransactionRequestBody,
    idempotency_key_header: str | None = Header(
        default=None,
        alias="Idempotency-Key",
    ),
):
    db = SessionLocal()

    transaction_id = None

    try:
        idempotency_key = (
            idempotency_key_header
            or payload.idempotency_key
        )

        if not idempotency_key:
            raise HTTPException(
                status_code=422,
                detail="Idempotency-Key header or idempotency_key body field is required",
            )

        if (
            payload.from_account
            == payload.to_account
        ):
            raise HTTPException(
                status_code=400,
                detail="Source and destination accounts must be different",
            )

        logger.info(
            "transaction_request from_account=%s to_account=%s currency=%s amount=%s idempotency_key=%s",
            payload.from_account,
            payload.to_account,
            payload.currency,
            payload.amount,
            idempotency_key,
        )

        existing = (
            db.query(Transaction)
            .filter(
                Transaction.idempotency_key
                == idempotency_key
            )
            .first()
        )

        if existing:
            same_request = (
                existing.from_account
                == payload.from_account
                and existing.to_account
                == payload.to_account
                and existing.currency
                == payload.currency
                and existing.amount
                == payload.amount
            )

            if not same_request:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key already used for a different transaction request",
                )

            logger.info(
                "idempotent_replay transaction_id=%s idempotency_key=%s",
                existing.transaction_id,
                idempotency_key,
            )

            return existing

        account_ids = sorted(
            [
                payload.from_account,
                payload.to_account,
            ]
        )

        accounts = (
            db.query(Account)
            .filter(
                Account.account_id.in_(account_ids)
            )
            .with_for_update()
            .all()
        )

        accounts_by_id = {
            account.account_id: account
            for account in accounts
        }

        source = accounts_by_id.get(
            payload.from_account
        )

        destination = accounts_by_id.get(
            payload.to_account
        )

        if not source:
            raise HTTPException(
                status_code=404,
                detail="Source account not found",
            )

        if not destination:
            raise HTTPException(
                status_code=404,
                detail="Destination account not found",
            )

        if source.status != "ACTIVE":
            raise HTTPException(
                status_code=400,
                detail="Source account is not active",
            )

        if destination.status != "ACTIVE":
            raise HTTPException(
                status_code=400,
                detail="Destination account is not active",
            )

        if (
            source.currency
            != payload.currency
            or destination.currency
            != payload.currency
        ):
            raise HTTPException(
                status_code=400,
                detail="Currency mismatch",
            )

        if source.balance < payload.amount:
            raise HTTPException(
                status_code=400,
                detail="Insufficient funds",
            )

        transaction_id = (
            f"TXN-{uuid4().hex[:12].upper()}"
        )

        create_audit_event(
            db=db,
            transaction_id=transaction_id,
            event_type="TRANSACTION_CREATED",
            event_status="PENDING",
            actor="transaction-service",
            reason="Transaction request accepted",
        )

        logger.info(
            "fraud_check_started transaction_id=%s",
            transaction_id,
        )

        try:
            fraud_response = requests.post(
                f"{FRAUD_SERVICE_URL}/fraud/check",
                json={
                    "transaction_id": transaction_id,
                    "from_account": payload.from_account,
                    "to_account": payload.to_account,
                    "currency": payload.currency,
                    "amount": float(payload.amount),
                },
                timeout=FRAUD_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            logger.error(
                "fraud_service_unavailable transaction_id=%s error=%s",
                transaction_id,
                type(exc).__name__,
            )

            create_audit_event(
                db=db,
                transaction_id=transaction_id,
                event_type="FRAUD_CHECK",
                event_status="ERROR",
                actor="fraud-service",
                reason="Fraud service unavailable",
            )

            db.commit()

            raise HTTPException(
                status_code=503,
                detail="Fraud service temporarily unavailable",
            )

        if fraud_response.status_code != 200:
            try:
                fraud_data = fraud_response.json()
            except ValueError:
                fraud_data = {
                    "message": "Fraud service rejected the transaction"
                }

            reason = fraud_data.get(
                "reason",
                "fraud rule rejection",
            )

            risk_score = fraud_data.get(
                "risk_score"
            )

            create_audit_event(
                db=db,
                transaction_id=transaction_id,
                event_type="FRAUD_CHECK",
                event_status="REJECTED",
                actor="fraud-service",
                reason=reason,
            )

            db.commit()

            logger.warning(
                "fraud_rejected transaction_id=%s risk_score=%s reason=%s",
                transaction_id,
                risk_score,
                reason,
            )

            raise HTTPException(
                status_code=403,
                detail={
                    "message": "Transaction rejected by fraud service",
                    "risk_score": risk_score,
                    "reason": reason,
                },
            )

        try:
            fraud_data = fraud_response.json()
        except ValueError:
            fraud_data = {}

        create_audit_event(
            db=db,
            transaction_id=transaction_id,
            event_type="FRAUD_CHECK",
            event_status="APPROVED",
            actor="fraud-service",
            reason="transaction passed fraud rules",
        )

        transaction = Transaction(
            transaction_id=transaction_id,
            idempotency_key=idempotency_key,
            from_account=payload.from_account,
            to_account=payload.to_account,
            currency=payload.currency,
            amount=payload.amount,
            status="PENDING",
        )

        db.add(transaction)
        db.flush()

        source.balance -= payload.amount
        destination.balance += payload.amount

        transaction.status = "COMPLETED"

        create_audit_event(
            db=db,
            transaction_id=transaction_id,
            event_type="TRANSACTION_COMPLETED",
            event_status="COMPLETED",
            actor="transaction-service",
            reason="Ledger balances updated successfully",
        )

        db.commit()
        db.refresh(transaction)

        logger.info(
            "transaction_completed transaction_id=%s amount=%s",
            transaction_id,
            payload.amount,
        )

        return transaction

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()

        existing = (
            db.query(Transaction)
            .filter(
                Transaction.idempotency_key
                == (
                    idempotency_key_header
                    or payload.idempotency_key
                )
            )
            .first()
        )

        if existing:
            logger.info(
                "concurrent_idempotency_replay transaction_id=%s",
                existing.transaction_id,
            )

            same_request = (
                existing.from_account
                == payload.from_account
                and existing.to_account
                == payload.to_account
                and existing.currency
                == payload.currency
                and existing.amount
                == payload.amount
            )

            if not same_request:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key already used for a different transaction request",
                )

            return existing

        logger.exception(
            "database_integrity_error transaction_id=%s",
            transaction_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Transaction processing failed",
        )

    except Exception:
        db.rollback()

        logger.exception(
            "transaction_processing_error transaction_id=%s",
            transaction_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Transaction processing failed",
        )

    finally:
        db.close()


@app.get(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse,
)
def get_transaction(transaction_id: str):
    db = SessionLocal()

    try:
        transaction = (
            db.query(Transaction)
            .filter(
                Transaction.transaction_id
                == transaction_id
            )
            .first()
        )

        if not transaction:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found",
            )

        return transaction

    finally:
        db.close()


@app.get(
    "/audit/transactions/{transaction_id}"
)
def get_transaction_audit(transaction_id: str):
    db = SessionLocal()

    try:
        transaction = (
            db.query(Transaction)
            .filter(
                Transaction.transaction_id
                == transaction_id
            )
            .first()
        )

        audit_events = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.transaction_id
                == transaction_id
            )
            .order_by(
                AuditEvent.created_at.asc(),
                AuditEvent.id.asc(),
            )
            .all()
        )

        if not transaction and not audit_events:
            raise HTTPException(
                status_code=404,
                detail="Transaction audit history not found",
            )

        return {
            "transaction_id": transaction_id,
            "transaction_exists": transaction is not None,
            "transaction_status": (
                transaction.status
                if transaction
                else None
            ),
            "audit_events": [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "event_status": event.event_status,
                    "actor": event.actor,
                    "reason": event.reason,
                    "created_at": event.created_at,
                }
                for event in audit_events
            ],
        }

    finally:
        db.close()

LEDGEROPS_HTTP_REQUESTS_TOTAL = Counter(
    "ledgerops_http_requests_total",
    "Total HTTP requests handled by transaction service",
    ["method", "path", "status"],
)

LEDGEROPS_HTTP_REQUEST_DURATION = Histogram(
    "ledgerops_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    import time

    start = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start

    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)

    LEDGEROPS_HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        path=path,
        status=str(response.status_code),
    ).inc()

    LEDGEROPS_HTTP_REQUEST_DURATION.labels(
        method=request.method,
        path=path,
    ).observe(duration)

    return response


@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
