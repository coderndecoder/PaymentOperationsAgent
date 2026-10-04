# Payment Failure Policy

## Overview
Payment failures occur when a transaction cannot be completed successfully. This policy explains
common causes, how our system responds automatically, and what support agents should do when
a customer reports a failed payment.

## Common Failure Reasons

### Card-Related Failures
- **Insufficient funds**: The card does not have enough balance.
- **Card declined**: The issuing bank declined the transaction (can be for many reasons).
- **Expired card**: The card expiration date has passed.
- **Incorrect card details**: Wrong card number, CVV, or billing address.

### Bank Transfer Failures
- **Invalid account number**: The bank account details provided are incorrect.
- **Bank connectivity issues**: Temporary issues with the customer's bank.
- **Transfer limit exceeded**: The customer's bank has a daily or transaction limit.

### Technical Failures
- **Gateway timeout**: The payment gateway did not respond in time.
- **Duplicate transaction**: The system detected a possible duplicate payment.
- **Fraud detection block**: The transaction was flagged by fraud prevention systems.

## Automatic Retry Logic
- For **subscription renewals**, our system automatically retries failed payments:
  - Retry 1: 1 day after initial failure
  - Retry 2: 3 days after initial failure
  - Retry 3: 7 days after initial failure
- If all 3 retries fail, the subscription is suspended and the customer is notified by email.

## Support Agent Steps for Failed Payments

### Step 1: Identify the Failure Reason
- Look up the payment ID to find the failure code or status.
- Ask the customer to confirm their payment method details.

### Step 2: Guide the Customer
- For **card issues**: Ask the customer to update their card details and retry.
- For **bank transfer issues**: Verify the account number and re-initiate the transfer.
- For **technical failures**: Advise the customer to retry after 30 minutes; escalate if the issue persists.

### Step 3: Escalation
- If the payment has failed more than 3 times, escalate to the billing team.
- If funds were debited from the customer but the payment shows as failed, escalate immediately — this is a priority case.

## Important Notes
- A **failed payment does NOT mean the customer was charged**. In most cases, funds were only held temporarily and will be released within 3–5 business days.
- If a customer reports funds were debited and the payment is still showing as failed, this is a bank reconciliation issue and must be escalated to billing within 24 hours.
- Never advise a customer to attempt the same failed payment more than 3 times without investigating the root cause.
