from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Account


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LedgerOps Account Service",
    version="1.0.0",
)


class AccountCreate(BaseModel):
    customer_id: str
    currency: str = "CAD"
    initial_balance: float = Field(default=0.0, ge=0.0)


class AccountResponse(BaseModel):
    account_id: str
    customer_id: str
    currency: str
    balance: float
    status: str

    class Config:
        from_attributes = True


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post(
    "/accounts",
    response_model=AccountResponse,
    status_code=201,
)
def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
):
    account_id = f"ACC-{uuid4().hex[:8].upper()}"

    new_account = Account(
        account_id=account_id,
        customer_id=account.customer_id,
        currency=account.currency,
        balance=account.initial_balance,
        status="ACTIVE",
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_account


@app.get(
    "/accounts/{account_id}",
    response_model=AccountResponse,
)
def get_account(
    account_id: str,
    db: Session = Depends(get_db),
):
    account = db.get(Account, account_id)

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    return account


@app.get("/accounts/{account_id}/balance")
def get_balance(
    account_id: str,
    db: Session = Depends(get_db),
):
    account = db.get(Account, account_id)

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    return {
        "account_id": account.account_id,
        "currency": account.currency,
        "balance": float(account.balance),
    }
