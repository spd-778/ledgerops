from decimal import Decimal
from uuid import uuid4
import os
import requests

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import Account, AuditEvent, Base, Transaction


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="LedgerOps Transaction Service",
    version="1.0.0",
)

FRAUD_SERVICE_URL = os.getenv(
    "FRAUD_SERVICE_URL",
    "http://127.0.0.1:8003",
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


class TransactionResponse(BaseModel):
    transaction_id: str
    idempotency_key: str
    from_account: str
    to_account: str
    currency: str
    amount: Decimal
    status: str

    model_config = ConfigDict(from_attributes=True)


@app.get("/health")
def health():
    return {
        "service": "transaction-service",
        "status": "healthy",
    }


@app.post(
    "/transactions",
    response_model=TransactionResponse,
    status_code=201,
)
def create_transaction(
    request: TransactionCreate,
):
    db: Session = SessionLocal()

    try:
        existing_transaction = (
            db.query(Transaction)
            .filter(
                Transaction.idempotency_key
                == request.idempotency_key
            )
            .first()
        )

        if existing_transaction:
            same_request = (
                existing_transaction.from_account
                == request.from_account
                and existing_transaction.to_account
                == request.to_account
                and existing_transaction.currency
                == request.currency
                and Decimal(
                    str(existing_transaction.amount)
                )
                == request.amount
            )

            if not same_request:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Idempotency key already exists "
                        "with different transaction data"
                    ),
                )

            return existing_transaction

        if request.from_account == request.to_account:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Source and destination accounts "
                    "must be different"
                ),
            )

        account_ids = sorted(
            [
                request.from_account,
                request.to_account,
            ]
        )

        locked_accounts = (
            db.query(Account)
            .filter(
                Account.account_id.in_(account_ids)
            )
            .order_by(Account.account_id)
            .with_for_update()
            .all()
        )

        accounts = {
            account.account_id: account
            for account in locked_accounts
        }

        from_account = accounts.get(
            request.from_account
        )

        to_account = accounts.get(
            request.to_account
        )

        if not from_account:
            raise HTTPException(
                status_code=404,
                detail="Source account not found",
            )

        if not to_account:
            raise HTTPException(
                status_code=404,
                detail="Destination account not found",
            )

        if from_account.status != "ACTIVE":
            raise HTTPException(
                status_code=400,
                detail="Source account is not active",
            )

        if to_account.status != "ACTIVE":
            raise HTTPException(
                status_code=400,
                detail="Destination account is not active",
            )

        if from_account.currency != request.currency:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Source account currency does not "
                    "match transaction currency"
                ),
            )

        if to_account.currency != request.currency:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Destination account currency does not "
                    "match transaction currency"
                ),
            )

        if Decimal(
            str(from_account.balance)
        ) < request.amount:
            raise HTTPException(
                status_code=400,
                detail="Insufficient funds",
            )

        transaction_id = (
            f"TXN-{uuid4().hex[:12].upper()}"
        )

        fraud_response = requests.post(
            f"{FRAUD_SERVICE_URL}/fraud/check",
            json={
                "transaction_id": transaction_id,
                "from_account": request.from_account,
                "to_account": request.to_account,
                "currency": request.currency,
                "amount": str(request.amount),
            },
            timeout=5,
        )

        if fraud_response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail="Fraud service unavailable",
            )

        fraud_result = fraud_response.json()

        if fraud_result["decision"] == "REJECTED":
            db.add(
                AuditEvent(
                    transaction_id=transaction_id,
                    event_type="FRAUD_CHECK",
                    event_status="REJECTED",
                    actor="fraud-service",
                    reason=fraud_result["reason"],
                )
            )

            db.commit()

            raise HTTPException(
                status_code=403,
                detail={
                    "message": "Transaction rejected by fraud service",
                    "risk_score": fraud_result["risk_score"],
                    "reason": fraud_result["reason"],
                },
            )

        db.add(
            AuditEvent(
                transaction_id=transaction_id,
                event_type="TRANSACTION_CREATED",
                event_status="PENDING",
                actor="transaction-service",
                reason="Transaction request accepted",
            )
        )

        db.add(
            AuditEvent(
                transaction_id=transaction_id,
                event_type="FRAUD_CHECK",
                event_status="APPROVED",
                actor="fraud-service",
                reason=fraud_result["reason"],
            )
        )

        new_transaction = Transaction(
            transaction_id=transaction_id,
            idempotency_key=request.idempotency_key,
            from_account=request.from_account,
            to_account=request.to_account,
            currency=request.currency,
            amount=request.amount,
            status="PENDING",
        )

        db.add(new_transaction)

        from_account.balance = (
            Decimal(str(from_account.balance))
            - request.amount
        )

        to_account.balance = (
            Decimal(str(to_account.balance))
            + request.amount
        )

        new_transaction.status = "COMPLETED"

        db.add(
            AuditEvent(
                transaction_id=transaction_id,
                event_type="TRANSACTION_COMPLETED",
                event_status="COMPLETED",
                actor="transaction-service",
                reason="Ledger balances updated successfully",
            )
        )

        db.commit()
        db.refresh(new_transaction)

        return new_transaction

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()

        existing_transaction = (
            db.query(Transaction)
            .filter(
                Transaction.idempotency_key
                == request.idempotency_key
            )
            .first()
        )

        if existing_transaction:
            return existing_transaction

        raise HTTPException(
            status_code=500,
            detail="Transaction could not be created",
        )

    except Exception as exc:
        db.rollback()

        print(f"TRANSACTION ERROR: {type(exc).__name__}: {exc}", flush=True)

        raise HTTPException(
            status_code=500,
            detail=f"Transaction processing failed: {type(exc).__name__}: {exc}",
        )

    finally:
        db.close()


@app.get(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse,
)
def get_transaction(
    transaction_id: str,
):
    db: Session = SessionLocal()

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



@app.get("/audit/transactions/{transaction_id}")
def get_transaction_audit(transaction_id: str):
    db = SessionLocal()
    try:
        transaction = db.query(Transaction).filter(
            Transaction.transaction_id == transaction_id
        ).first()

        audit_events = (
            db.query(AuditEvent)
            .filter(AuditEvent.transaction_id == transaction_id)
            .order_by(AuditEvent.created_at.asc(), AuditEvent.id.asc())
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
            "transaction_status": transaction.status if transaction else None,
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

@app.get("/transactions")
def list_transactions():
    db: Session = SessionLocal()

    try:
        return (
            db.query(Transaction)
            .order_by(Transaction.created_at.desc())
            .all()
        )

    finally:
        db.close()
