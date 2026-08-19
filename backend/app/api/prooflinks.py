from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.schemas.prooflink import (
    CreateProofLinkRequest,
    CreateProofLinkResponse,
    ProofLinkDetailResponse,
    RevokeRequest,
    RevokeResponse,
    InstructionDetail,
    InstitutionDetail,
)
from app.services.prooflink_service import (
    create_prooflink,
    get_prooflink,
    revoke_prooflink,
)
from app.services.institution_service import get_institution
from app.api.auth import get_current_user
from app.services.auth_service import get_citizen_by_user_id, get_official_by_user_id

router = APIRouter(prefix="/prooflinks", tags=["ProofLinks"])

@router.post("", response_model=CreateProofLinkResponse, status_code=status.HTTP_201_CREATED, summary="Create ProofLink")
def create_new_prooflink(
    payload: CreateProofLinkRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint 2 — Create ProofLink
    Validates institution, signs canonical instruction with Ed25519, hashes with SHA-256, and stores in registry.
    """
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Use POST /official/instructions. ProofLinks are generated only after verified citizen matching.")

@router.get("/{proof_id}", response_model=ProofLinkDetailResponse, summary="Get ProofLink Details")
def get_prooflink_details(
    proof_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint 4 — Get ProofLink
    Used by frontend to display authoritative instruction details.
    """
    prooflink = get_prooflink(db, proof_id)
    if not prooflink:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ProofLink '{proof_id}' not found."
        )
    citizen = get_citizen_by_user_id(db, current_user.id)
    official = get_official_by_user_id(db, current_user.id)
    if (current_user.role == "CITIZEN" and (not citizen or prooflink.citizen_id != citizen.id)) or (current_user.role == "OFFICIAL" and (not official or prooflink.institution_id != official.institution_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this ProofLink.")

    institution = get_institution(db, prooflink.institution_id)
    inst_detail = InstitutionDetail(
        id=prooflink.institution_id,
        name=institution.name if institution else "Unknown Institution",
        type=institution.type if institution else None,
        public_key=institution.public_key if institution else None,
        status=institution.status if institution else None
    )

    instr_detail = InstructionDetail(
        action=prooflink.action,
        amount=prooflink.amount,
        currency=prooflink.currency,
        recipient=prooflink.recipient,
        purpose=prooflink.purpose,
        reference_id=prooflink.reference_id
    )

    return ProofLinkDetailResponse(
        proof_id=prooflink.proof_id,
        institution=inst_detail,
        instruction=instr_detail,
        content_hash=prooflink.content_hash,
        signature=prooflink.signature,
        status=prooflink.status,
        created_at=prooflink.created_at,
        expires_at=prooflink.expires_at
    )

@router.post("/{proof_id}/revoke", response_model=RevokeResponse, summary="Revoke ProofLink")
def revoke_existing_prooflink(
    proof_id: str,
    payload: RevokeRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint 5 — Revoke
    Revokes the ProofLink and creates an immutable revocation audit record.
    """
    if current_user.role != "OFFICIAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only officials can revoke ProofLinks.")
    official = get_official_by_user_id(db, current_user.id)
    existing = get_prooflink(db, proof_id)
    if not existing or not official or existing.institution_id != official.institution_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ProofLink not found.")
    revoked_item = revoke_prooflink(db, proof_id, reason=payload.reason, revoked_by=official.id)
    return RevokeResponse(
        proof_id=revoked_item.proof_id,
        status=revoked_item.status
    )
