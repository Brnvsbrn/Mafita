# Double Debit

Use this when a customer reports duplicate debit, repeated card debit, or same merchant charged twice.

Required checks:
- Pull recent transactions.
- Compare amount, merchant, and timestamps.
- Check ledger entries for duplicate posted debits.
- If duplicate is confirmed, create a dispute and reversal request.

Resolution:
- Duplicate debit disputes are high priority.
- Card duplicate debit may require merchant/acquirer review.
- If fraud is suspected, offer to block the card.
