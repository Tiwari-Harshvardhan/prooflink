from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.schemas.institution import InstitutionResponse
from app.schemas.prooflink import ProofLinkDetailResponse, InstructionDetail, InstitutionDetail
from app.services.institution_service import get_institution, get_all_institutions
from app.services.prooflink_service import get_prooflinks_by_institution

router = APIRouter(prefix="/institutions", tags=["Institutions"])

@router.get("", response_model=List[InstitutionResponse], summary="List All Institutions")
def list_institutions(db: Session = Depends(get_db)):
    """List all registered institutions and their trusted public keys."""
    institutions = get_all_institutions(db)
    return [InstitutionResponse.from_orm_model(inst) for inst in institutions]

@router.get("/{institution_id}", response_model=InstitutionResponse, summary="Get Institution Details")
def get_institution_by_id(
    institution_id: str,
    db: Session = Depends(get_db)
):
    """
    Endpoint 6 — Institution
    Retrieves public registry data for a trusted institution. Private keys are never exposed.
    """
    inst = get_institution(db, institution_id)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Institution '{institution_id}' not found in registry."
        )
    return InstitutionResponse.from_orm_model(inst)

@router.get("/{institution_id}/prooflinks", response_model=List[ProofLinkDetailResponse], summary="Get ProofLinks by Institution")
def get_institution_prooflinks(
    institution_id: str,
    db: Session = Depends(get_db)
):
    """
    List all ProofLinks issued by a specific institution.
    """
    inst = get_institution(db, institution_id)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Institution '{institution_id}' not found in registry."
        )
    
    prooflinks = get_prooflinks_by_institution(db, institution_id)
    inst_detail = InstitutionDetail(
        id=inst.id,
        name=inst.name,
        type=inst.type,
        public_key=inst.public_key,
        status=inst.status
    )

    results = []
    for pl in prooflinks:
        instr_detail = InstructionDetail(
            action=pl.action,
            amount=pl.amount,
            currency=pl.currency,
            recipient=pl.recipient,
            purpose=pl.purpose,
            reference_id=pl.reference_id
        )
        results.append(
            ProofLinkDetailResponse(
                proof_id=pl.proof_id,
                institution=inst_detail,
                instruction=instr_detail,
                content_hash=pl.content_hash,
                signature=pl.signature,
                status=pl.status,
                created_at=pl.created_at,
                expires_at=pl.expires_at
            )
        )
    return results
