"""
Dashboard API endpoints for citizens and officials.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.database.connection import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.prooflink import ProofLink
from app.models.instruction import Instruction
from app.models.payment import Payment
from app.services.auth_service import get_citizen_by_user_id, get_official_by_user_id
from pydantic import BaseModel, Field


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class ProofLinkDashboardResponse(BaseModel):
    proof_id: str
    institution_id: str
    action: str
    amount: float
    currency: str
    recipient: str
    purpose: str
    reference_id: str
    status: str
    created_at: datetime
    expires_at: datetime
    citizen_aadhaar_masked: Optional[str] = None

    class Config:
        from_attributes = True


class InstructionDashboardResponse(BaseModel):
    id: str
    instruction_id: str
    action: str
    amount: float
    currency: str
    purpose: str
    reference_id: str
    issued_at: datetime
    due_at: datetime
    status: str
    payment_status: str = "PENDING"
    payment_id: Optional[str] = None
    paid_at: Optional[datetime] = None


@router.get("/citizen/prooflinks", response_model=List[ProofLinkDashboardResponse])
def get_citizen_prooflinks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all prooflinks for the authenticated citizen.
    Only returns prooflinks bound to the citizen.
    """
    if current_user.role != "CITIZEN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can access this endpoint."
        )

    citizen = get_citizen_by_user_id(db, current_user.id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen record not found."
        )

    # Get all prooflinks that match this citizen's phone
    prooflinks = db.query(ProofLink).filter(
        ProofLink.citizen_phone == current_user.phone
    ).all()

    return prooflinks


@router.get("/official/prooflinks", response_model=List[ProofLinkDashboardResponse])
def get_official_prooflinks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all prooflinks created by the authenticated official.
    Only returns prooflinks from their institution.
    """
    if current_user.role != "OFFICIAL":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only officials can access this endpoint."
        )

    official = get_official_by_user_id(db, current_user.id)
    if not official:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Official record not found."
        )

    # ProofLink tokens are intentionally never disclosed to an official.
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Use /dashboard/official/instructions; officials do not receive ProofLink tokens.")


@router.get("/official/instructions", response_model=List[InstructionDashboardResponse])
def get_official_instructions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all instructions created by the authenticated official.
    """
    if current_user.role != "OFFICIAL":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only officials can access this endpoint."
        )

    official = get_official_by_user_id(db, current_user.id)
    if not official:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Official record not found."
        )

    # Get all instructions created by this official
    instructions = db.query(Instruction).filter(
        Instruction.official_id == official.id
    ).all()
    response = []
    for instruction in instructions:
        payment = db.query(Payment).filter(Payment.instruction_id == instruction.instruction_id).order_by(Payment.created_at.desc()).first()
        response.append(InstructionDashboardResponse(
            id=instruction.id, instruction_id=instruction.instruction_id, action=instruction.action,
            amount=instruction.amount, currency=instruction.currency, purpose=instruction.purpose,
            reference_id=instruction.reference_id, issued_at=instruction.issued_at, due_at=instruction.due_at,
            status=instruction.status, payment_status=payment.status if payment else "PENDING",
            payment_id=payment.id if payment else None, paid_at=payment.paid_at if payment else None,
        ))
    return response
