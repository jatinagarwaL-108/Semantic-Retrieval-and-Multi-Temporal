"""
Tamper-Proof Audit Trail Routes
"""

from fastapi import APIRouter
from backend.app.db.audit_ledger import get_audit_ledger

router = APIRouter(prefix="/audit-trail", tags=["Audit Trail"])


@router.get("")
async def get_audit_trail():
    """
    Returns the complete tamper-proof audit trail ledger
    alongside a real-time cryptographic integrity verification.
    """
    ledger = get_audit_ledger()
    is_valid, count, corrupted_idx = ledger.verify_integrity()

    return {
        "integrity_status": "SECURE_VERIFIED" if is_valid else "TAMPERED_COMPROMISED",
        "is_valid": is_valid,
        "total_records": count,
        "corrupted_block_index": corrupted_idx,
        "cryptographic_algorithm": "SHA-256 Hash Chaining",
        "ledger": ledger.chain,
    }


@router.post("/verify")
async def verify_audit_trail():
    """
    Explicitly re-runs cryptographic verification across the full chain.
    """
    ledger = get_audit_ledger()
    is_valid, count, corrupted_idx = ledger.verify_integrity()
    return {
        "is_valid": is_valid,
        "total_blocks_checked": count,
        "first_tampered_block": corrupted_idx,
        "verification_timestamp": "NOW",
    }
