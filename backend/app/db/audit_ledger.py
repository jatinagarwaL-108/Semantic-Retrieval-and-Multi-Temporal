"""
Cryptographic Tamper-Proof Audit Trail Ledger
========================================================================================
Maintains an immutable, append-only hash-chained ledger for all analyst decisions.
Each entry is cryptographically bound to the previous block via SHA-256:
  Block[n].hash = SHA256(Block[n-1].hash + Timestamp + User + TilePairID + Decision + Evidence)
Any modification to prior records invalidates the entire subsequent chain.
========================================================================================
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple


GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


def compute_entry_hash(
    prev_hash: str,
    timestamp: str,
    analyst_user: str,
    tile_pair_id: str,
    decision: str,
    change_id: str,
    evidence_payload: Dict[str, Any],
) -> str:
    """Calculates SHA-256 cryptographic digest of ledger block contents."""
    canonical_evidence = json.dumps(evidence_payload, sort_keys=True)
    message = f"{prev_hash}|{timestamp}|{analyst_user}|{tile_pair_id}|{decision}|{change_id}|{canonical_evidence}"
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


class TamperProofAuditLedger:
    """
    Manages persistence and verification of the cryptographic audit chain.
    """

    def __init__(self, ledger_file: str = "data/audit_ledger.json"):
        self.ledger_file = ledger_file
        self.chain: List[Dict[str, Any]] = []
        self.load_ledger()

    def load_ledger(self):
        if os.path.exists(self.ledger_file):
            try:
                with open(self.ledger_file, "r") as f:
                    self.chain = json.load(f)
            except Exception as e:
                print(f"[AuditLedger] Error reading ledger: {e}, resetting chain")
                self.chain = []
        else:
            self.chain = []

    def save_ledger(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.ledger_file)), exist_ok=True)
        with open(self.ledger_file, "w") as f:
            json.dump(self.chain, f, indent=2)

    def append_decision(
        self,
        analyst_user: str,
        tile_pair_id: str,
        change_id: str,
        decision: str,  # "CONFIRM_REAL_CHANGE" or "REJECT_FALSE_ALARM"
        change_type: str,
        confidence_percent: float,
        evidence: Dict[str, Any],
        analyst_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Appends a new analyst verification block to the tamper-proof ledger.
        """
        prev_hash = self.chain[-1]["block_hash"] if self.chain else GENESIS_HASH
        timestamp = datetime.now(timezone.utc).isoformat()

        evidence_payload = {
            "change_type": change_type,
            "confidence_percent": confidence_percent,
            "analyst_notes": analyst_notes or "",
            "polygon_evidence": evidence,
        }

        block_hash = compute_entry_hash(
            prev_hash=prev_hash,
            timestamp=timestamp,
            analyst_user=analyst_user,
            tile_pair_id=tile_pair_id,
            decision=decision,
            change_id=change_id,
            evidence_payload=evidence_payload,
        )

        block = {
            "block_index": len(self.chain) + 1,
            "prev_hash": prev_hash,
            "block_hash": block_hash,
            "timestamp": timestamp,
            "analyst_user": analyst_user,
            "tile_pair_id": tile_pair_id,
            "change_id": change_id,
            "decision": decision,
            "evidence": evidence_payload,
            "verified": True,
        }

        self.chain.append(block)
        self.save_ledger()
        return block

    def verify_integrity(self) -> Tuple[bool, int, Optional[int]]:
        """
        Verifies the cryptographic integrity of the entire ledger chain.
        Returns:
            (is_valid, total_blocks, corrupted_block_index)
        """
        if not self.chain:
            return True, 0, None

        expected_prev = GENESIS_HASH
        for idx, block in enumerate(self.chain):
            # 1. Check prev_hash link
            if block["prev_hash"] != expected_prev:
                return False, len(self.chain), idx + 1

            # 2. Recompute hash
            recomputed = compute_entry_hash(
                prev_hash=block["prev_hash"],
                timestamp=block["timestamp"],
                analyst_user=block["analyst_user"],
                tile_pair_id=block["tile_pair_id"],
                decision=block["decision"],
                change_id=block["change_id"],
                evidence_payload=block["evidence"],
            )

            if recomputed != block["block_hash"]:
                return False, len(self.chain), idx + 1

            expected_prev = block["block_hash"]

        return True, len(self.chain), None


_GLOBAL_LEDGER: Optional[TamperProofAuditLedger] = None

def get_audit_ledger() -> TamperProofAuditLedger:
    global _GLOBAL_LEDGER
    if _GLOBAL_LEDGER is None:
        _GLOBAL_LEDGER = TamperProofAuditLedger()
    return _GLOBAL_LEDGER
