from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.verification import VerifyRequest, VerifyResponse
from app.services.verification_service import verify_prooflink
from app.api.auth import get_current_user
from app.services.auth_service import get_citizen_by_user_id
from app.models.prooflink import ProofLink

router = APIRouter(tags=["Verification"])

@router.post("/verify", response_model=VerifyResponse, status_code=status.HTTP_200_OK, summary="Verify ProofLink Instruction")
def verify_instruction(
    payload: VerifyRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint 3 — Verify
    Primary citizen-facing endpoint to cryptographically verify an instruction's authenticity and integrity.
    """
    if current_user.role != "CITIZEN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "CITIZEN_AUTH_REQUIRED", "message": "Sign in as the verified citizen to verify a ProofLink."})
    citizen = get_citizen_by_user_id(db, current_user.id)
    prooflink = db.query(ProofLink).filter(ProofLink.proof_id == payload.prooflink).first()
    if not prooflink:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "PROOFLINK_NOT_FOUND", "message": "No such ProofLink exists."})
    if not citizen or prooflink.citizen_id != citizen.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "PROOFLINK_NOT_OWNED", "message": "This ProofLink is not associated with your verified identity."})
    return verify_prooflink(db, prooflink.proof_id)
