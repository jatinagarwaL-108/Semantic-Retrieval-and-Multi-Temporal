"""
Analyst Review & Decision Submission Route
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from backend.app.db.audit_ledger import get_audit_ledger

router = APIRouter(prefix="/analyst", tags=["Analyst Review"])


class AnalystReviewRequest(BaseModel):
    analyst_user: str = Field(default="Analyst_Officer_07")
    tile_pair_id: str
    change_id: str
    decision: str = Field(..., example="CONFIRM_REAL_CHANGE")  # CONFIRM_REAL_CHANGE or REJECT_FALSE_ALARM
    change_type: str
    confidence_percent: float
    evidence: Dict[str, Any]
    analyst_notes: Optional[str] = None


@router.post("/review")
async def submit_analyst_review(req: AnalystReviewRequest):
    """
    Records an analyst's confirmation or rejection of detected change into
    the cryptographic tamper-proof ledger with evidence references.
    """
    if req.decision not in ["CONFIRM_REAL_CHANGE", "REJECT_FALSE_ALARM"]:
        raise HTTPException(
            status_code=400,
            detail="Decision must be 'CONFIRM_REAL_CHANGE' or 'REJECT_FALSE_ALARM'",
        )

    ledger = get_audit_ledger()
    block = ledger.append_decision(
        analyst_user=req.analyst_user,
        tile_pair_id=req.tile_pair_id,
        change_id=req.change_id,
        decision=req.decision,
        change_type=req.change_type,
        confidence_percent=req.confidence_percent,
        evidence=req.evidence,
        analyst_notes=req.analyst_notes,
    )

    return {
        "status": "RECORDED_IN_IMMUTABLE_LEDGER",
        "block": block,
        "chain_length": len(ledger.chain),
    }
