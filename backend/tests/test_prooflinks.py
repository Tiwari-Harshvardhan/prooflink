import re
import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from app.schemas.prooflink import CreateProofLinkRequest
from app.services.prooflink_service import (
    create_prooflink,
    get_prooflink,
    revoke_prooflink,
    get_prooflinks_by_institution
)

def test_create_and_get_prooflink(db_session):
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
    assert prooflink is not None
    assert prooflink.proof_id.startswith("PL-")
    assert prooflink.status == "ACTIVE"
    assert len(prooflink.content_hash) == 64
    assert len(prooflink.signature) > 0
    
    fetched = get_prooflink(db_session, prooflink.proof_id)
    assert fetched is not None
    assert fetched.proof_id == prooflink.proof_id
    assert fetched.amount == 80000.0

def test_create_prooflink_sanitizes_reference_id_and_stores_citizen_identity(db_session):
    expires_at = datetime.now(timezone.utc) + timedelta(days=2)
    req = CreateProofLinkRequest(
        institution_id="POLICE-MP-001",
        action="PAYMENT",
        amount=150,
        currency="INR",
        recipient="Harshvardhan Tiwari",
        purpose="Traffic challan",
        reference_id="abcd#1234",
        aadhaar_number="1234 5678 9012",
        phone_number="+91-9876543210",
        expires_at=expires_at
    )

    prooflink = create_prooflink(db_session, req)

    assert prooflink is not None
    assert re.fullmatch(r"PL-[A-Za-z0-9]+", prooflink.proof_id)
    assert not "#" in prooflink.proof_id
    assert prooflink.aadhaar_number is None
    assert prooflink.phone_number == "+919876543210"


def test_create_prooflink_unknown_institution_raises_404(db_session):
    expires_at = datetime.now(timezone.utc) + timedelta(days=2)
    req = CreateProofLinkRequest(
        institution_id="UNKNOWN-INST-999",
        action="PAYMENT",
        amount=50000,
        currency="INR",
        recipient="XXXX9999",
        purpose="FAKE_FINE",
        reference_id="CASE-9999",
        expires_at=expires_at
    )
    
    with pytest.raises(HTTPException) as exc_info:
        create_prooflink(db_session, req)
    assert exc_info.value.status_code == 404

def test_revoke_prooflink(db_session):
    expires_at = datetime.now(timezone.utc) + timedelta(days=2)
    req = CreateProofLinkRequest(
        institution_id="POLICE-MP-001",
        action="PAYMENT",
        amount=80000,
        currency="INR",
        recipient="XXXX1234",
        purpose="CASE_SETTLEMENT",
        reference_id="CASE-2026-REVOKE",
        expires_at=expires_at
    )
    
    prooflink = create_prooflink(db_session, req)
    revoked = revoke_prooflink(db_session, prooflink.proof_id, reason="Instruction cancelled by department")
    
    assert revoked.status == "REVOKED"
    assert revoked.revocation is not None
    assert revoked.revocation.reason == "Instruction cancelled by department"

def test_list_prooflinks_by_institution(db_session):
    expires_at = datetime.now(timezone.utc) + timedelta(days=2)
    for i in range(3):
        req = CreateProofLinkRequest(
            institution_id="SBI-HQ-001",
            action="PAYMENT",
            amount=10000 * (i + 1),
            currency="INR",
            recipient=f"ACC-00{i}",
            purpose="LOAN_VERIFICATION",
            reference_id=f"LOAN-2026-00{i}",
            expires_at=expires_at
        )
        create_prooflink(db_session, req)
        
    links = get_prooflinks_by_institution(db_session, "SBI-HQ-001")
    assert len(links) == 3
