from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, Numeric, String
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(String(20), primary_key=True)
    customer_id = Column(String(50), nullable=False)
    currency = Column(String(3), nullable=False)
    balance = Column(Numeric(18, 2), nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    transaction_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    idempotency_key = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    from_account = Column(
        String,
        nullable=False,
    )

    to_account = Column(
        String,
        nullable=False,
    )

    currency = Column(
        String,
        nullable=False,
    )

    amount = Column(
        Numeric(18, 2),
        nullable=False,
    )

    status = Column(
        String,
        nullable=False,
        default="PENDING",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )
