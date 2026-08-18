from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.verification import VerifyRequest, VerifyResponse
from app.services.verification_service import verify_prooflink

router = APIRouter(tags=["Verification"])

@router.post("/verify", response_model=VerifyResponse, status_code=status.HTTP_200_OK, summary="Verify ProofLink Instruction")
def verify_instruction(
    payload: VerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint 3 — Verify
    Primary citizen-facing endpoint to cryptographically verify an instruction's authenticity and integrity.
    """
    return verify_prooflink(db, payload.proof_id)
