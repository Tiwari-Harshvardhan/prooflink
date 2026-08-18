import pytest
from datetime import datetime, timezone, timedelta
from app.schemas.prooflink import CreateProofLinkRequest
from app.services.prooflink_service import create_prooflink, revoke_prooflink
from app.services.verification_service import verify_prooflink
from app.models.prooflink import ProofLink

def test_verification_valid_complete(db_session):
    """Test 12: Complete valid verification."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=2)
    req = CreateProofLinkRequest(
        institution_id="POLICE-MP-001",
        action="PAYMENT",
        amount=80000,
        currency="INR",
        recipient="XXXX1234",
        purpose="CASE_SETTLEMENT",
        reference_id="CASE-2026-00123",
        expires_at=expires_at
    )
    
    prooflink = create_prooflink(db_session, req)
    result = verify_prooflink(db_session, prooflink.proof_id)
    
    assert result.status == "VERIFIED"
    assert result.proof_id == prooflink.proof_id
    assert result.institution is not None
    assert result.institution.id == "POLICE-MP-001"
    assert result.institution.name == "Madhya Pradesh Police Department"
    assert result.instruction is not None
    assert result.instruction.amount == 80000.0
    assert result.instruction.recipient == "XXXX1234"
    assert result.checks.exists is True
    assert result.checks.institution_recognized is True
    assert result.checks.signature_valid is True
    assert result.checks.hash_valid is True
    assert result.checks.amount_match is True
    assert result.checks.recipient_match is True
    assert result.checks.not_expired is True
    assert result.checks.not_revoked is True

def test_verification_unknown_proof_id(db_session):
    """Test 11: Unknown Proof ID returns NOT_FOUND."""
    result = verify_prooflink(db_session, "PL-NON-EXISTENT-9999")
    
    assert result.status == "NOT_FOUND"
    assert result.checks.exists is False
    assert result.institution is None
    assert result.instruction is None

def test_verification_hash_mismatch(db_session):
    """Test 8: Hash mismatch when data in DB is tampered without updating hash."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=2)
    req = CreateProofLinkRequest(
        institution_id="POLICE-MP-001",
        action="PAYMENT",
        amount=80000,
        currency="INR",
        recipient="XXXX1234",
        purpose="CASE_SETTLEMENT",
        reference_id="CASE-2026-TAMPER-HASH",
        expires_at=expires_at
    )
    
    prooflink = create_prooflink(db_session, req)
    
    # Simulate database tampering: modifying amount from 80000 to 999999
    db_record = db_session.query(ProofLink).filter(ProofLink.proof_id == prooflink.proof_id).first()
    db_record.amount = 999999.0
    db_session.commit()
    
    result = verify_prooflink(db_session, prooflink.proof_id)
    assert result.status == "HASH_MISMATCH"
    assert result.checks.exists is True
    assert result.checks.hash_valid is False

def test_verification_invalid_signature(db_session):
    """Test 7: Invalid signature detection."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=2)
    req = CreateProofLinkRequest(
        institution_id="POLICE-MP-001",
        action="PAYMENT",
        amount=80000,
        currency="INR",
        recipient="XXXX1234",
        purpose="CASE_SETTLEMENT",
        reference_id="CASE-2026-BAD-SIG",
        expires_at=expires_at
    )
    
    prooflink = create_prooflink(db_session, req)
    
    # Corrupt signature in database
    db_record = db_session.query(ProofLink).filter(ProofLink.proof_id == prooflink.proof_id).first()
    db_record.signature = "ZmFrZXNpZ25hdHVyZXRvZmFpbHZlcmlmaWNhdGlvbg=="
    db_session.commit()
    
    result = verify_prooflink(db_session, prooflink.proof_id)
    assert result.status == "INVALID_SIGNATURE"
    assert result.checks.exists is True
    assert result.checks.signature_valid is False

def test_verification_expired(db_session):
    """Test 9: Expired ProofLink."""
    past_expiration = datetime.now(timezone.utc) - timedelta(hours=2)
    req = CreateProofLinkRequest(
        institution_id="POLICE-MP-001",
        action="PAYMENT",
        amount=80000,
        currency="INR",
        recipient="XXXX1234",
        purpose="CASE_SETTLEMENT",
        reference_id="CASE-2026-EXPIRED",
        expires_at=past_expiration
    )
    
    prooflink = create_prooflink(db_session, req)
    result = verify_prooflink(db_session, prooflink.proof_id)
    
    assert result.status == "EXPIRED"
    assert result.checks.not_expired is False

def test_verification_revoked(db_session):
    """Test 10: Revoked ProofLink."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=2)
    req = CreateProofLinkRequest(
        institution_id="POLICE-MP-001",
        action="PAYMENT",
        amount=80000,
        currency="INR",
        recipient="XXXX1234",
        purpose="CASE_SETTLEMENT",
        reference_id="CASE-2026-REVOKED-TEST",
        expires_at=expires_at
    )
    
    prooflink = create_prooflink(db_session, req)
    revoke_prooflink(db_session, prooflink.proof_id, reason="Instruction superseded")
    
    result = verify_prooflink(db_session, prooflink.proof_id)
    assert result.status == "REVOKED"
    assert result.checks.not_revoked is False
    assert "superseded" in result.message
