"""
tools.py
--------
Defines the four deterministic LangChain tools the LLM can call.

Tools:
  1. get_payment(payment_id)
  2. get_customer(customer_id)
  3. search_support_cases(query)
  4. check_refund_eligibility(payment_id)  <- 100% deterministic Python rules
"""

import json
from datetime import date, datetime
from pathlib import Path
from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Helpers — load JSON data files once at import time
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent.parent / "data"


def _load(filename: str) -> list[dict]:
    with open(DATA_DIR / filename, "r") as f:
        return json.load(f)


CUSTOMERS = _load("customers.json")
PAYMENTS = _load("payments.json")
SUPPORT_CASES = _load("support_cases.json")

# ---------------------------------------------------------------------------
# Business rule constants (single source of truth)
# ---------------------------------------------------------------------------

REFUND_WINDOW_DAYS = 30
ELIGIBLE_STATUS = "completed"
NON_REFUNDABLE_KEYWORDS = ["subscription"]

# ---------------------------------------------------------------------------
# Tool 1: get_payment
# ---------------------------------------------------------------------------


@tool
def get_payment(payment_id: str) -> str:
    """
    Retrieve a payment record by its ID (e.g. 'PAY-001').
    Returns all payment details: customer ID, amount, status, method, date, description.
    """
    payment_id = payment_id.strip().upper()
    for payment in PAYMENTS:
        if payment["id"] == payment_id:
            return json.dumps(payment, indent=2)
    return (
        f"Error: Payment '{payment_id}' not found. "
        f"Available IDs: {[p['id'] for p in PAYMENTS]}"
    )


# ---------------------------------------------------------------------------
# Tool 2: get_customer
# ---------------------------------------------------------------------------


@tool
def get_customer(customer_id: str) -> str:
    """
    Retrieve a customer record by their ID (e.g. 'CUST-001').
    Returns name, email, tier (standard/premium), and join date.
    """
    customer_id = customer_id.strip().upper()
    for customer in CUSTOMERS:
        if customer["id"] == customer_id:
            return json.dumps(customer, indent=2)
    return (
        f"Error: Customer '{customer_id}' not found. "
        f"Available IDs: {[c['id'] for c in CUSTOMERS]}"
    )


# ---------------------------------------------------------------------------
# Tool 3: search_support_cases
# ---------------------------------------------------------------------------


@tool
def search_support_cases(query: str) -> str:
    """
    Search support cases by keyword or customer/payment ID.
    Searches across issue text, customer_id, payment_id, and status fields.
    Returns up to 5 matching cases as JSON.
    """
    query_lower = query.strip().lower()
    matches = []
    for case in SUPPORT_CASES:
        searchable = " ".join([
            case.get("issue", ""),
            case.get("customer_id", ""),
            case.get("payment_id", ""),
            case.get("status", ""),
            case.get("resolution") or "",
        ]).lower()
        if query_lower in searchable:
            matches.append(case)

    if not matches:
        return f"No support cases found matching '{query}'."
    return json.dumps(matches[:5], indent=2)


# ---------------------------------------------------------------------------
# Tool 4: check_refund_eligibility  (deterministic — LLM cannot override)
# ---------------------------------------------------------------------------


@tool
def check_refund_eligibility(payment_id: str) -> str:
    """
    Check whether a payment qualifies for a refund using deterministic business rules.

    Rules (applied in order):
      1. Payment must exist.
      2. Payment status must be 'completed'.
      3. Payment must be within the 30-day refund window.
      4. Payment must not be for a subscription.

    Returns a clear ELIGIBLE or INELIGIBLE verdict with the reason.
    The LLM must relay this verdict as-is — it must not invent a different answer.
    """
    payment_id = payment_id.strip().upper()

    # Find the payment
    payment = next((p for p in PAYMENTS if p["id"] == payment_id), None)
    if payment is None:
        return (
            f"INELIGIBLE — Payment '{payment_id}' does not exist. "
            "Cannot assess refund eligibility."
        )

    status = payment["status"]
    description = payment.get("description", "").lower()
    payment_date = datetime.strptime(payment["date"], "%Y-%m-%d").date()
    age_days = (date.today() - payment_date).days

    # Rule 1: Status check
    if status != ELIGIBLE_STATUS:
        reason_map = {
            "failed":   "the payment never completed — no funds were captured.",
            "pending":  "the payment is still processing. Wait for it to complete first.",
            "refunded": "this payment has already been refunded.",
        }
        reason = reason_map.get(status, f"status is '{status}'.")
        return (
            f"INELIGIBLE — Payment {payment_id} cannot be refunded because {reason}\n"
            f"  Status: {status} | Amount: ${payment['amount']} | Date: {payment['date']}"
        )

    # Rule 2: 30-day window
    if age_days > REFUND_WINDOW_DAYS:
        return (
            f"INELIGIBLE — Payment {payment_id} is {age_days} days old, which exceeds "
            f"the {REFUND_WINDOW_DAYS}-day refund window.\n"
            f"  Status: {status} | Amount: ${payment['amount']} | Date: {payment['date']}"
        )

    # Rule 3: Subscription check
    for keyword in NON_REFUNDABLE_KEYWORDS:
        if keyword in description:
            return (
                f"INELIGIBLE — Payment {payment_id} is for a subscription "
                f"('{payment['description']}'), which cannot be refunded once the "
                f"billing cycle has started.\n"
                f"  Status: {status} | Amount: ${payment['amount']} | Date: {payment['date']}"
            )

    # All rules passed → eligible
    return (
        f"ELIGIBLE — Payment {payment_id} qualifies for a refund.\n"
        f"  Amount:  ${payment['amount']} {payment['currency']}\n"
        f"  Date:    {payment['date']} ({age_days} days ago — within {REFUND_WINDOW_DAYS}-day window)\n"
        f"  Status:  {status}\n"
        f"  Item:    {payment['description']}\n"
        "Next step: Submit a refund request through the billing system. "
        "Processing takes 5–10 business days."
    )

