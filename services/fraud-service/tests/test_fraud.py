from decimal import Decimal

from app.main import FraudCheckRequest, fraud_check


def make_request(amount):
    return FraudCheckRequest(
        transaction_id="TXN-TEST-001",
        from_account="ACC-C8E952EE",
        to_account="ACC-8853F2E7",
        currency="CAD",
        amount=Decimal(str(amount)),
    )


def test_small_transaction_is_approved():
    response = fraud_check(make_request("100.00"))

    assert response["decision"] == "APPROVED"
    assert response["risk_score"] == 0


def test_elevated_transaction_requires_review():
    response = fraud_check(make_request("2000.00"))

    assert response["decision"] == "REVIEW"
    assert response["risk_score"] == 40


def test_large_transaction_is_rejected():
    response = fraud_check(make_request("6000.00"))

    assert response["decision"] == "REJECTED"
    assert response["risk_score"] == 70
    assert response["reason"] == "large transaction"


def test_high_risk_transaction_is_rejected():
    response = fraud_check(make_request("10000.00"))

    assert response["decision"] == "REJECTED"
    assert response["risk_score"] == 100
    assert response["reason"] == "transaction exceeds high-risk threshold"
