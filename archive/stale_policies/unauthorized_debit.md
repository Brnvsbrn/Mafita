# Unauthorized Debit

Use this when the customer says they did not authorize a debit, card transaction, POS debit, or transfer.

Required checks:
- Verify customer identity before exposing transaction details.
- Check transaction and card status.
- If card or wallet compromise is likely, block card and create fraud report.
- Escalate to human fraud review.

Resolution:
- Never guarantee refund before fraud review.
- Collect time, amount, merchant/recipient, and whether the customer still has the device/card.
