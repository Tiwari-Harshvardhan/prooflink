"""
test_crypto.py — Updated crypto layer tests for the QDS prototype.

These tests replace or adapt the former Ed25519-specific tests to use
the new teleportation-based QDS signing/verification layer while
preserving all test IDs and coverage goals.
"""
import pytest
from app.crypto.hashing import (
    create_canonical_instruction,
    canonicalize_to_bytes,
    calculate_content_hash,
)
from app.crypto.signing import sign_canonical_instruction
from app.crypto.verification import verify_ed25519_signature, verify_qds_signature_full
from app.crypto.qds import (
    QDSSignatureRecord,
    PROTOCOL_VERSION,
    sign_instruction,
    verify_instruction,
    register_signer,
    reset_nonce_store,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

POLICE_INST_ID = "POLICE-MP-001"
SBI_INST_ID = "SBI-HQ-001"

BASE_CANONICAL_KWARGS = dict(
    proof_id="PL-2026-00123",
    institution_id=POLICE_INST_ID,
    action="PAYMENT",
    amount=80000,
    currency="INR",
    recipient="XXXX1234",
    purpose="CASE_SETTLEMENT",
    reference_id="CASE-2026-00123",
    issued_at="2026-08-18T08:00:00Z",
    expires_at="2026-08-20T18:00:00Z",
)


def _make_canonical():
    return create_canonical_instruction(**BASE_CANONICAL_KWARGS)


def _make_sig(canonical=None, institution_id=POLICE_INST_ID) -> str:
    """
    Sign using the QDS adapter (sign_canonical_instruction).
    private_key=None is accepted because the QDS path ignores it.
    """
    if canonical is None:
        canonical = _make_canonical()
    return sign_canonical_instruction(private_key=None, canonical_data=canonical)


# ---------------------------------------------------------------------------
# Test 1: Canonicalization and SHA-256 fingerprint (unchanged)
# ---------------------------------------------------------------------------

def test_canonicalization_and_hashing():
    """Deterministic canonical representation and SHA-256 fingerprint."""
    c1 = _make_canonical()
    c2 = _make_canonical()

    b1 = canonicalize_to_bytes(c1)
    b2 = canonicalize_to_bytes(c2)
    assert b1 == b2, "Canonical bytes must be identical for same inputs"

    h1 = calculate_content_hash(c1)
    h2 = calculate_content_hash(c2)
    assert h1 == h2
    assert len(h1) == 64, "SHA-256 hex digest must be 64 characters"


# ---------------------------------------------------------------------------
# Test 2: QDS signing produces a valid JSON record
# ---------------------------------------------------------------------------

def test_qds_signing_produces_valid_record():
    """sign_canonical_instruction returns a valid QDSSignatureRecord JSON."""
    canonical = _make_canonical()
    sig_json = _make_sig(canonical)

    assert isinstance(sig_json, str) and len(sig_json) > 0

    record = QDSSignatureRecord.from_json(sig_json)
    assert record.is_valid_format(), "Signature record must pass structural validation"
    assert record.protocol == PROTOCOL_VERSION
    assert record.state_label in ("0", "1", "+", "-", "+i", "-i")
    assert record.basis in ("X", "Y", "Z")
    assert record.expected_outcome in ("0", "1")
    assert len(record.nonce) == 64  # 32 bytes = 64 hex chars
    assert record.signer_id == POLICE_INST_ID


# ---------------------------------------------------------------------------
# Test 3: QDS verification — valid signature (drop-in verify_ed25519_signature)
# ---------------------------------------------------------------------------

def test_qds_verification_via_adapter():
    """verify_ed25519_signature returns True for a freshly created QDS signature."""
    reset_nonce_store()
    canonical = _make_canonical()
    sig_json = _make_sig(canonical)

    # The adapter accepts public_key=None in the QDS path
    result = verify_ed25519_signature(
        public_key=None,
        signature_b64=sig_json,
        canonical_data=canonical,
    )
    assert result is True


# ---------------------------------------------------------------------------
# Test 4: Tamper detection — modified amount
# ---------------------------------------------------------------------------

def test_tamper_detection_modified_amount():
    """Modified amount causes fingerprint mismatch -> FORGERY_SUSPECTED."""
    reset_nonce_store()
    canonical = _make_canonical()
    sig_json = _make_sig(canonical)

    # Attacker modifies amount
    tampered = dict(canonical)
    tampered["amount"] = 150000.0

    # SHA-256 fingerprint must differ
    orig_hash = calculate_content_hash(canonical)
    tampered_hash = calculate_content_hash(tampered)
    assert orig_hash != tampered_hash

    # QDS verification must fail (fingerprint mismatch)
    result = verify_qds_signature_full(
        signature_json=sig_json,
        canonical_data=tampered,
        institution_id=POLICE_INST_ID,
    )
    assert result.status in ("FORGERY_SUSPECTED", "INVALID_SIGNATURE_FORMAT")


# ---------------------------------------------------------------------------
# Test 5: Tamper detection — modified recipient
# ---------------------------------------------------------------------------

def test_tamper_detection_modified_recipient():
    """Modified recipient causes fingerprint mismatch -> FORGERY_SUSPECTED."""
    reset_nonce_store()
    canonical = _make_canonical()
    sig_json = _make_sig(canonical)

    tampered = dict(canonical)
    tampered["recipient"] = "ATTACKER_ACCOUNT_999"

    result = verify_qds_signature_full(
        signature_json=sig_json,
        canonical_data=tampered,
        institution_id=POLICE_INST_ID,
    )
    assert result.status in ("FORGERY_SUSPECTED", "INVALID_SIGNATURE_FORMAT")


# ---------------------------------------------------------------------------
# Test 6: Invalid / corrupted signature string
# ---------------------------------------------------------------------------

def test_invalid_signature_string():
    """Corrupted signature JSON returns INVALID_SIGNATURE_FORMAT."""
    reset_nonce_store()
    canonical = _make_canonical()

    # Not valid JSON
    result = verify_qds_signature_full(
        signature_json="ZmFrZXNpZ25hdHVyZXRvZmFpbHZlcmlmaWNhdGlvbg==",
        canonical_data=canonical,
        institution_id=POLICE_INST_ID,
    )
    assert result.status == "INVALID_SIGNATURE_FORMAT"


# ---------------------------------------------------------------------------
# Test 7: Wrong institution (impersonation)
# ---------------------------------------------------------------------------

def test_wrong_institution_impersonation():
    """Unregistered signer returns UNAUTHORIZED_SIGNER."""
    reset_nonce_store()
    canonical = _make_canonical()
    sig_json = _make_sig(canonical, institution_id=POLICE_INST_ID)

    # Verify against a different, unregistered institution
    result = verify_qds_signature_full(
        signature_json=sig_json,
        canonical_data=canonical,
        institution_id="FAKE-INSTITUTION-999",
    )
    assert result.status == "UNAUTHORIZED_SIGNER"
    assert result.attack_type == "IMPERSONATION"


# ---------------------------------------------------------------------------
# Test 8: Replay detection
# ---------------------------------------------------------------------------

def test_replay_detection():
    """Reusing the same QDS nonce triggers REPLAY_DETECTED."""
    reset_nonce_store()
    register_signer(POLICE_INST_ID)
    canonical = _make_canonical()

    # Sign once
    record = sign_instruction(
        canonical_data=canonical,
        institution_id=POLICE_INST_ID,
        proof_id="PL-REPLAY-TEST",
    )
    sig_json = record.to_json()

    # First verification consumes the nonce -> VERIFIED
    r1 = verify_instruction(
        canonical_data=canonical,
        signature_json=sig_json,
        institution_id=POLICE_INST_ID,
    )
    assert r1.status == "VERIFIED", f"First verification must pass, got {r1.status}: {r1.message}"

    # Second verification with the same nonce -> REPLAY_DETECTED
    r2 = verify_instruction(
        canonical_data=canonical,
        signature_json=sig_json,
        institution_id=POLICE_INST_ID,
    )
    assert r2.status == "REPLAY_DETECTED"
    assert r2.attack_type == "REPLAY"
