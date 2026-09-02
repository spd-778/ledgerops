from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.main import TransactionCreate


def test_transaction_requires_positive_amount():
    with pytest.raises(ValidationError):
        TransactionCreate(
            idempotency_key="TEST-NEGATIVE",
            from_account="ACC-C8E952EE",
            to_account="ACC-8853F2E7",
            currency="CAD",
            amount=Decimal("-100.00"),
        )


def test_transaction_accepts_valid_amount():
    request = TransactionCreate(
        idempotency_key="TEST-VALID",
        from_account="ACC-C8E952EE",
        to_account="ACC-8853F2E7",
        currency="CAD",
        amount=Decimal("100.00"),
    )

    assert request.amount == Decimal("100.00")
    assert request.currency == "CAD"
    assert request.idempotency_key == "TEST-VALID"


def test_transaction_rejects_zero_amount():
    with pytest.raises(ValidationError):
        TransactionCreate(
            idempotency_key="TEST-ZERO",
            from_account="ACC-C8E952EE",
            to_account="ACC-8853F2E7",
            currency="CAD",
            amount=Decimal("0.00"),
        )


def test_transaction_requires_idempotency_key():
    with pytest.raises(ValidationError):
        TransactionCreate(
            from_account="ACC-C8E952EE",
            to_account="ACC-8853F2E7",
            currency="CAD",
            amount=Decimal("100.00"),
        )


def test_transaction_rejects_empty_idempotency_key():
    with pytest.raises(ValidationError):
        TransactionCreate(
            idempotency_key="",
            from_account="ACC-C8E952EE",
            to_account="ACC-8853F2E7",
            currency="CAD",
            amount=Decimal("100.00"),
        )
