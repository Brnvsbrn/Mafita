import json
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent
ROOT = SCRATCH.parent
LEXICON_PATH = ROOT / "src" / "entity_lexicon.json"
OUT_PATH = SCRATCH / "entity_stress_v2_queries.json"

VOICES = ["femi", "sade", "segun", "funmi"]

CRITICAL_ENTITIES = [
    "OPay",
    "PalmPay",
    "Moniepoint",
    "Kuda",
    "Paga",
    "Access Bank",
    "GTBank",
    "Zenith Bank",
    "BVN",
    "NIN",
    "KYC",
    "Session ID",
    "POS",
    "USSD",
    "NIP",
    "transaction reference",
    "reversal",
    "debit",
    "failed transfer",
]


def load_entities():
    lexicon = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
    by_type = {}
    for entity in lexicon["entities"]:
        by_type.setdefault(entity["type"], []).append(entity["canonical"])
    return by_type, [entity["canonical"] for entity in lexicon["entities"]]


def add_sample(samples, text, translation, expected_entities, category):
    sample_id = f"S{len(samples) + 1:03d}"
    samples.append(
        {
            "id": sample_id,
            "text": text,
            "translation": translation,
            "voice": VOICES[(len(samples)) % len(VOICES)],
            "category": category,
            "expected_entities": list(dict.fromkeys(expected_entities)),
        }
    )


def build_broad_coverage(by_type):
    samples = []
    providers = by_type["provider"]
    banks = by_type["bank"]
    digital_banks = by_type["digital_bank"]
    processors = by_type["payment_processor"]
    card_schemes = by_type["card_scheme"]
    channels = by_type["channel"]
    identity = by_type["identity"]
    transaction_terms = by_type["transaction_term"]
    support_terms = by_type["support_term"]
    payment_terms = by_type["payment_term"]
    account_terms = by_type["account_term"]
    security_terms = by_type["security_term"]
    statuses = by_type["status"]
    fraud_terms = by_type["fraud_term"]

    for index, provider in enumerate(providers):
        bank = banks[index % len(banks)]
        status = statuses[index % len(statuses)]
        support = support_terms[index % len(support_terms)]
        add_sample(
            samples,
            f"Mo lo {provider} lati ran owo si {bank}, sugbon transaction naa wa ni {status}, mo fe {support}.",
            f"I used {provider} to send money to {bank}, but the transaction is {status}, and I want {support}.",
            [provider, bank, status, support],
            "provider_bank_status_support",
        )

    remaining_banks = banks[len(providers):]
    for index in range(0, len(remaining_banks), 2):
        first = remaining_banks[index]
        second = remaining_banks[(index + 1) % len(remaining_banks)]
        add_sample(
            samples,
            f"Transfer lati {first} si {second} ni transaction reference sugbon ko si receipt.",
            f"The transfer from {first} to {second} has a transaction reference but no receipt.",
            [first, second, "transaction reference", "receipt"],
            "bank_pair_reference_receipt",
        )

    for index, bank in enumerate(banks[:10]):
        digital = digital_banks[index % len(digital_banks)]
        account_term = account_terms[index % len(account_terms)]
        add_sample(
            samples,
            f"{digital} app mi so pe {account_term} lori transfer si {bank}.",
            f"My {digital} app says {account_term} on the transfer to {bank}.",
            [digital, account_term, bank],
            "digital_bank_account_term",
        )

    for index, processor in enumerate(processors):
        scheme = card_schemes[index % len(card_schemes)]
        payment_term = payment_terms[index % len(payment_terms)]
        add_sample(
            samples,
            f"{processor} payment lori {scheme} card ni {payment_term}, mo nilo help.",
            f"The {processor} payment on a {scheme} card has a {payment_term} issue, and I need help.",
            [processor, scheme, payment_term],
            "processor_card_payment_term",
        )

    for index, channel in enumerate(channels):
        provider = providers[(index + 4) % len(providers)]
        add_sample(
            samples,
            f"{channel} lori {provider} ko sise, customer care bot ko ran mi lowo.",
            f"{channel} on {provider} is not working, and the customer care bot did not help.",
            [channel, provider, "customer care", "bot"],
            "channel_customer_care",
        )

    add_sample(
        samples,
        "Mo fe so BVN ati NIN mo account mi fun KYC, sugbon OTP ko de.",
        "I want to link BVN and NIN to my account for KYC, but the OTP did not arrive.",
        identity + ["OTP"],
        "identity_security",
    )
    add_sample(
        samples,
        "Mo gbagbe PIN ati password mi, sugbon app ko gba verification.",
        "I forgot my PIN and password, but the app does not accept verification.",
        security_terms,
        "security_terms",
    )
    add_sample(
        samples,
        "NIBSS nilo Session ID ati NIP details fun NUBAN account number.",
        "NIBSS needs Session ID and NIP details for the NUBAN account number.",
        ["NIBSS", "Session ID", "NIP", "NUBAN"],
        "payment_infrastructure_terms",
    )
    add_sample(
        samples,
        "Mo ri unauthorized debit, won ni o je scam, sugbon wrong recipient nilo court order.",
        "I saw an unauthorized debit; they said it is a scam, but the wrong recipient case needs a court order.",
        fraud_terms + ["wrong recipient", "court order"],
        "fraud_legal_transfer_issue",
    )
    add_sample(
        samples,
        "Beneficiary ko ri credit, debit card ati virtual card mejeeji ni issue.",
        "The beneficiary did not receive credit, and both the debit card and virtual card have issues.",
        ["beneficiary", "credit", "debit card", "virtual card"],
        "beneficiary_card_terms",
    )
    return samples


def add_critical_variants(samples):
    variant_specs = [
        ("OPay", [
            ("OPay transfer mi kuna si GTBank.", ["OPay", "failed transfer", "GTBank"]),
            ("App OPay mi ko fi Session ID han.", ["OPay", "Session ID"]),
            ("OPay POS agent na mi double debit.", ["OPay", "POS", "double debit"]),
            ("Mo fe reversal lori OPay receipt mi.", ["OPay", "reversal", "receipt"]),
        ]),
        ("PalmPay", [
            ("PalmPay si Access Bank wa ni pending.", ["PalmPay", "Access Bank", "pending"]),
            ("PalmPay receipt mi ni transaction reference ti ko pe.", ["PalmPay", "receipt", "transaction reference"]),
            ("Mo fe link BVN mi lori PalmPay fun KYC.", ["PalmPay", "BVN", "KYC"]),
            ("PalmPay customer care bot ko dahun.", ["PalmPay", "customer care", "bot"]),
        ]),
        ("Moniepoint", [
            ("Moniepoint POS mi ni timeout lori NIP transfer.", ["Moniepoint", "POS", "timeout", "NIP"]),
            ("Moniepoint agent so pe transaction successful.", ["Moniepoint", "successful"]),
            ("Mo fe dispute fun Moniepoint double debit.", ["Moniepoint", "dispute", "double debit"]),
        ]),
        ("Kuda", [
            ("Kuda si Zenith Bank transfer wa ni pending.", ["Kuda", "Zenith Bank", "pending"]),
            ("Kuda app beere fun NIN ati BVN.", ["Kuda", "NIN", "BVN"]),
            ("Kuda debit card ko sise lori ATM.", ["Kuda", "debit card", "ATM"]),
        ]),
        ("Paga", [
            ("Paga USSD code ko fi wallet balance han.", ["Paga", "USSD", "wallet balance"]),
            ("Paga account restricted nitori KYC.", ["Paga", "account restricted", "KYC"]),
            ("Paga transfer nilo Session ID.", ["Paga", "Session ID"]),
        ]),
        ("Access Bank", [
            ("Access Bank ko ri credit lati OPay.", ["Access Bank", "credit", "OPay"]),
            ("Access Bank beneficiary name yato.", ["Access Bank", "beneficiary"]),
            ("Access Bank transaction reference ko han.", ["Access Bank", "transaction reference"]),
        ]),
        ("GTBank", [
            ("GTBank transfer lati PalmPay failed.", ["GTBank", "PalmPay", "failed transfer"]),
            ("GTBank receipt nilo Session ID.", ["GTBank", "receipt", "Session ID"]),
            ("GTBank card lori POS ni chargeback.", ["GTBank", "POS", "chargeback"]),
        ]),
        ("Zenith Bank", [
            ("Zenith Bank alert de sugbon balance ko yipada.", ["Zenith Bank", "wallet balance"]),
            ("Zenith Bank NIP transfer ni timeout.", ["Zenith Bank", "NIP", "timeout"]),
            ("Zenith Bank wrong recipient nilo court order.", ["Zenith Bank", "wrong recipient", "court order"]),
        ]),
        ("BVN", [
            ("BVN mi ko match NIN mi lori KYC.", ["BVN", "NIN", "KYC"]),
            ("Mo fe correct BVN lori PalmPay.", ["BVN", "PalmPay"]),
            ("BVN verification ko gba OTP.", ["BVN", "OTP"]),
        ]),
        ("Session ID", [
            ("Nibo ni Session ID wa lori receipt?", ["Session ID", "receipt"]),
            ("NIBSS trace beere fun Session ID.", ["NIBSS", "Session ID"]),
            ("Session ID lori OPay transfer ko han.", ["Session ID", "OPay"]),
            ("Banki beneficiary nilo Session ID.", ["beneficiary", "Session ID"]),
        ]),
        ("transaction reference", [
            ("Transaction reference mi ko han ninu transaction history.", ["transaction reference", "transaction history"]),
            ("Mo ni transaction reference sugbon ko si receipt.", ["transaction reference", "receipt"]),
            ("Customer care beere fun transaction reference.", ["customer care", "transaction reference"]),
        ]),
        ("debit", [
            ("Mo ri debit ti mi o mo.", ["debit"]),
            ("Double debit sele lori POS.", ["double debit", "POS"]),
            ("Unauthorized debit wa lori virtual card.", ["unauthorized debit", "virtual card"]),
        ]),
    ]
    for entity, variants in variant_specs:
        for text, expected in variants:
            add_sample(
                samples,
                text,
                text,
                expected,
                f"critical_variant_{entity.lower().replace(' ', '_')}",
            )


def main():
    by_type, all_canonicals = load_entities()
    samples = build_broad_coverage(by_type)
    add_critical_variants(samples)

    covered = {entity for sample in samples for entity in sample["expected_entities"]}
    missing = sorted(set(all_canonicals) - covered)
    if missing:
        raise RuntimeError(f"Stress manifest missing canonical entities: {missing}")

    OUT_PATH.write_text(json.dumps(samples, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"Samples: {len(samples)}")
    print(f"Canonical terms covered: {len(covered)} / {len(set(all_canonicals))}")
    print(f"Expected entity mentions: {sum(len(sample['expected_entities']) for sample in samples)}")


if __name__ == "__main__":
    main()
