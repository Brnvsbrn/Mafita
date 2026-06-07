# Pending Transfer

Use this when a transaction is still pending or timeout is mentioned.

Required checks:
- Find the transaction.
- Check if a reversal already exists.
- Check if the transaction is inside the 24-48 hour NIP settlement window.

Resolution:
- If already processing, give the reversal ETA.
- If outside the settlement window, create a dispute.
- If transaction is successful, provide Session ID for bank trace.
