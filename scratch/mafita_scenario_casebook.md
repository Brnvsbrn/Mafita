# Mafita Scenario Casebook

Use this as the tester roleplay guide. Do not start from fixed prompt templates. Start naturally, complain vaguely, ask a question, or provide all details upfront.

If Mafita asks for details, use the details from one assigned case. Customer names are intentionally hidden; identity exists only inside the mock KYC/user database.

## Supported Tracks

Mafita is optimized for only these five support tracks:

1. Debited but recipient not credited.
2. Pending transfer, user wants to know whether to retry.
3. Pending reversal status check.
4. Double debit on failed POS transaction.
5. Account frozen from KYC or suspicious activity review.

If a tester goes outside these tracks, Mafita should constrain the conversation back to these supported cases.

## Case Details

| Case | Track | What happened | Details tester can provide |
| --- | --- | --- | --- |
| MFCASE001 | Debited, recipient not credited | Transfer left wallet but recipient did not receive it. | transaction ID `OPY7834KL`, time `1:47pm`, amount `NGN 15000`, bank `Zenith Bank` |
| MFCASE002 | Debited, recipient not credited | Vendor says payment has not arrived. | transaction ID `PAL4829QA`, time `10:18am`, amount `NGN 22000`, bank `Access Bank` |
| MFCASE003 | Debited, recipient not credited | Small transfer to a friend has not arrived. | transaction ID `MFT6082RD`, time `6:05pm`, amount `NGN 8750`, bank `GTBank` |
| MFCASE004 | Pending transfer retry advice | Rent transfer is pending and user wants to send again. | transaction ID `MPT9021XZ`, time `3:15pm`, amount `NGN 50000` |
| MFCASE005 | Pending transfer retry advice | School fees transfer is pending. | transaction ID `OPA7145MN`, time `8:40am`, amount `NGN 12000` |
| MFCASE006 | Pending reversal status | User has waited since Monday for a reversal. | transaction ID `MNP4410BV`, time `Monday 10am`, amount `NGN 32000`, ticket `CMP4192A` |
| MFCASE007 | Pending reversal status | Complaint exists but reversal has not landed. | transaction ID `RVL7832TX`, time `Tuesday 4:20pm`, amount `NGN 18500`, ticket `CMP8305K` |
| MFCASE008 | POS double debit | POS declined, wallet was debited. | transaction ID `OPY2291TR`, time `yesterday 6pm`, amount `NGN 50000`, evidence: decline slip and debit alert |
| MFCASE009 | POS double debit | POS failed this morning but wallet was debited. | transaction ID `POS8044KD`, time `today 9:10am`, amount `NGN 30000`, evidence: decline slip and debit alert |
| MFCASE010 | POS double debit | POS agent was not credited but wallet shows debit. | transaction ID `MPT5520HF`, time `Friday 7:30pm`, amount `NGN 20000`, evidence: decline slip and debit alert |
| MFCASE011 | KYC restriction | Account frozen because of name mismatch. | registered phone `07055234918`, evidence: government ID and written explanation |
| MFCASE012 | KYC restriction | Account restricted after suspicious activity flag. | registered phone `08031456789`, evidence: government ID and written explanation |
