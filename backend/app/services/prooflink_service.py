"""
ProofLink Service: Creation, retrieval, and revocation workflows.
"""
from datetime import datetime, timezone
from typing import Optional, List
import hashlib
import uuid
import secrets
import re
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.prooflink import ProofLink
from app.models.revocation import Revocation
from app.schemas.prooflink import CreateProofLinkRequest
from app.services.institution_service import get_institution, get_institution_private_key
from app.crypto.hashing import create_canonical_instruction, calculate_content_hash
from app.crypto.signing import sign_canonical_instruction


def normalize_phone_number(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    return f"+{digits}" if digits and not digits.startswith("0") else digits


def normalize_aadhaar_number(aadhaar: str) -> str:
    digits = re.sub(r"\D", "", aadhaar or "")
    return digits[-12:] if len(digits) >= 12 else digits


def safe_instruction_id(reference_id: str) -> str:
    cleaned = (reference_id or "").strip()
    cleaned = cleaned.replace("#", "-")
    cleaned = re.sub(r"[^A-Za-z0-9\-]", "-", cleaned)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    if not cleaned:
        cleaned = f"INST-{uuid.uuid4().hex[:8].upper()}"
    return cleaned


def generate_proof_id(reference_id: str) -> str:
    """Generate a safe ProofLink token while preserving valid reference formats like CASE-2026-00123."""
    # ProofLink tokens are opaque, high-entropy references.  They never embed
    # an instruction ID (which may contain URL-significant characters such as #).
    return f"PL-{secrets.token_urlsafe(24).replace('_', '').replace('-', '')}"

def create_prooflink(db: Session, request: CreateProofLinkRequest, *, citizen_id: str | None = None, official_id: str | None = None) -> ProofLink:
    """
    1. Validate institution
    2. Generate unique Proof ID
    3. Create canonical instruction
    4. Generate SHA-256 content hash
    5. Load institution private key
    6. Sign canonical instruction using Ed25519
    7. Store instruction, signature, content hash
    8. Return ProofLink record
    """
    # Step 1: Validate institution
    institution = get_institution(db, request.institution_id)
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Institution with ID '{request.institution_id}' not found."
        )
    if institution.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Institution '{request.institution_id}' is not active."
        )

    # Step 2: Generate unique Proof ID
    proof_id = generate_proof_id(request.reference_id)

    # Check if Proof ID already exists
    existing = db.query(ProofLink).filter(ProofLink.proof_id == proof_id).first()
    if existing:
        proof_id = f"{proof_id}-{uuid.uuid4().hex[:4].upper()}"

    # Instruction IDs are opaque data, not URL path components. Preserve values
    # such as `abcd#1234` exactly; only the independently generated token is
    # used in URLs.
    cleaned_instruction_id = (getattr(request, "instruction_id", None) or request.reference_id).strip()
    normalized_phone = normalize_phone_number(getattr(request, "phone_number", request.recipient))
    normalized_aadhaar = normalize_aadhaar_number(getattr(request, "aadhaar_number", ""))

    # Standardize timestamps
    created_at = datetime.now(timezone.utc)
    expires_at = request.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    # Step 3: Create canonical instruction
    canonical_dict = create_canonical_instruction(
        proof_id=proof_id,
        institution_id=institution.id,
        action=request.action,
        amount=request.amount,
        currency=request.currency,
        recipient=request.recipient,
        purpose=request.purpose,
        reference_id=request.reference_id,
        issued_at=created_at,
        expires_at=expires_at
    )

    # Step 4: Generate SHA-256 content hash
    content_hash = calculate_content_hash(canonical_dict)

    # Step 5: Load institution private key
    private_key = get_institution_private_key(institution.id)
    if not private_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Secure signing key for institution '{institution.id}' is not loaded."
        )

    # Step 6: Sign canonical instruction using Ed25519
    signature = sign_canonical_instruction(private_key, canonical_dict)

    # Step 7: Store instruction
    prooflink = ProofLink(
        proof_id=proof_id,
        institution_id=institution.id,
        action=request.action.upper(),
        amount=float(request.amount),
        currency=request.currency.upper(),
        recipient=request.recipient,
        purpose=request.purpose,
        reference_id=request.reference_id,
        instruction_id=cleaned_instruction_id,
        phone_number=normalized_phone,
        # Never persist raw Aadhaar in a ProofLink.  The citizen registry owns
        # the salted/hashed identity reference.
        aadhaar_number=None,
        citizen_phone=normalized_phone,
        citizen_aadhaar_hash=hashlib.sha256(normalized_aadhaar.encode("utf-8")).hexdigest() if normalized_aadhaar else None,
        citizen_aadhaar_masked=f"XXXX XXXX {normalized_aadhaar[-4:] if normalized_aadhaar else '0000'}" if normalized_aadhaar else None,
        citizen_id=citizen_id,
        official_id=official_id,
        content_hash=content_hash,
        signature=signature,
        status="ACTIVE",
        created_at=created_at,
        expires_at=expires_at
    )
    db.add(prooflink)
    db.commit()
    db.refresh(prooflink)

    return prooflink

def get_prooflink(db: Session, proof_id: str) -> Optional[ProofLink]:
    """Retrieve ProofLink by proof_id."""
    return db.query(ProofLink).filter(ProofLink.proof_id == proof_id.strip()).first()

def revoke_prooflink(db: Session, proof_id: str, reason: str, revoked_by: Optional[str] = None) -> ProofLink:
    """Revoke an active or existing ProofLink and create a revocation audit record."""
    prooflink = get_prooflink(db, proof_id)
    if not prooflink:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ProofLink '{proof_id}' not found."
        )

    # Update status to REVOKED
    prooflink.status = "REVOKED"

    # Create revocation record
    existing_revocation = db.query(Revocation).filter(Revocation.proof_id == prooflink.proof_id).first()
    if not existing_revocation:
        revocation_record = Revocation(
            proof_id=prooflink.proof_id,
            reason=reason,
            revoked_at=datetime.now(timezone.utc),
            revoked_by=revoked_by
        )
        db.add(revocation_record)
    else:
        existing_revocation.reason = reason
        existing_revocation.revoked_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(prooflink)
    return prooflink

def get_prooflinks_by_institution(db: Session, institution_id: str) -> List[ProofLink]:
    """List all ProofLinks issued by a specific institution."""
    return db.query(ProofLink).filter(ProofLink.institution_id == institution_id).all()
