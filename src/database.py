import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DB_PATHS = {
    "palmpay": os.path.join(BASE_DIR, "palmpay_db.json"),
    "opay": os.path.join(BASE_DIR, "opay_db.json")
}

def list_providers():
    """Returns the fintech providers currently backed by mock databases."""
    return sorted(DB_PATHS.keys())

def _load_db(provider):
    if provider not in DB_PATHS:
        raise ValueError(f"Invalid provider: {provider}")
    path = DB_PATHS[provider]
    if not os.path.exists(path):
        # Return default structure if file not found
        return {"users": {}, "transactions": {}, "disputes": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_db(provider, data):
    if provider not in DB_PATHS:
        raise ValueError(f"Invalid provider: {provider}")
    path = DB_PATHS[provider]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user(provider, phone_number):
    """Retrieves user information by phone number."""
    db = _load_db(provider)
    return db["users"].get(phone_number)

def get_transaction(provider, tx_ref):
    """Retrieves transaction information by its reference."""
    db = _load_db(provider)
    return db["transactions"].get(tx_ref)

def list_user_transactions(provider, phone_number):
    """Lists all transactions associated with a user's phone number."""
    db = _load_db(provider)
    user_txs = []
    for tx_ref, tx in db["transactions"].items():
        if tx["sender_phone"] == phone_number:
            user_txs.append(tx)
    return sorted(user_txs, key=lambda x: x["timestamp"], reverse=True)

def create_dispute(provider, tx_ref, category, notes=""):
    """Creates a new dispute log for a failed transaction."""
    db = _load_db(provider)
    
    # Check if transaction exists
    if tx_ref not in db["transactions"]:
        return {"status": "error", "message": f"Transaction reference {tx_ref} not found."}
        
    tx = db["transactions"][tx_ref]
    if tx["status"] != "FAILED":
        return {"status": "error", "message": "Disputes can only be registered for failed transactions."}

    for dispute in db["disputes"].values():
        if dispute["ref"] == tx_ref and dispute["status"] in {"OPEN", "IN_REVIEW"}:
            return {
                "status": "exists",
                "dispute_id": dispute["dispute_id"],
                "message": f"An active dispute already exists for transaction {tx_ref}.",
                "dispute": dispute
            }
        
    # Generate unique dispute ID
    prefix = "PMP_DISP_" if provider == "palmpay" else "OPY_DISP_"
    dispute_count = len(db["disputes"]) + 1
    dispute_id = f"{prefix}{dispute_count:03d}"
    
    # Log dispute
    dispute_record = {
        "dispute_id": dispute_id,
        "ref": tx_ref,
        "status": "OPEN",
        "category": category,
        "created_at": datetime.now().isoformat(),
        "notes": notes,
        "resolution_eta": "24 to 72 hours"
    }
    
    db["disputes"][dispute_id] = dispute_record
    
    # Update transaction reversal status to PENDING_REVERSAL if it wasn't already
    if tx["reversal_status"] == "NONE":
        tx["reversal_status"] = "PENDING_REVERSAL"
        
    _save_db(provider, db)
    
    return {
        "status": "success",
        "dispute_id": dispute_id,
        "message": f"Dispute successfully opened for transaction {tx_ref}.",
        "dispute": dispute_record
    }

def get_dispute(provider, dispute_id):
    """Retrieves a dispute by its ID."""
    db = _load_db(provider)
    return db["disputes"].get(dispute_id)
