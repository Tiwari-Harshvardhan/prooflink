import pytest
import base64
from app.crypto.keys import (
    generate_keypair,
    export_public_key_b64,
    export_private_key_b64,
    load_public_key_b64,
    load_private_key_b64
)
from app.crypto.hashing import (
    create_canonical_instruction,
    canonicalize_to_bytes,
    calculate_content_hash
)
from app.crypto.signing import sign_canonical_instruction
from app.crypto.verification import verify_ed25519_signature

def test_key_generation_and_serialization():
    """Test 1: Key generation and serialization."""
    priv_key, pub_key = generate_keypair()
    
    pub_b64 = export_public_key_b64(pub_key)
    priv_b64 = export_private_key_b64(priv_key)
    
    assert isinstance(pub_b64, str)
    assert isinstance(priv_b64, str)
    assert len(base64.b64decode(pub_b64)) == 32
    assert len(base64.b64decode(priv_b64)) == 32
    
    loaded_pub = load_public_key_b64(pub_b64)
    loaded_priv = load_private_key_b64(priv_b64)
    
    assert loaded_pub is not None
    assert loaded_priv is not None

def test_canonicalization_and_hashing():
    """Test deterministic canonical representation and SHA-256 hashing."""
    canonical1 = create_canonical_instruction(
        proof_id="PL-2026-00123",
        institution_id="POLICE-MP-001",
        action="PAYMENT",
        amount=80000,
        currency="INR",
        recipient="XXXX1234",
        purpose="CASE_SETTLEMENT",
        reference_id="CASE-2026-00123",
        issued_at="2026-08-18T08:00:00Z",
        expires_at="2026-08-20T18:00:00Z"
    )
    
    canonical2 = create_canonical_instruction(
        proof_id="PL-2026-00123",
        institution_id="POLICE-MP-001",
        action="PAYMENT",
        amount=80000,
        currency="INR",
        recipient="XXXX1234",
        purpose="CASE_SETTLEMENT",
        reference_id="CASE-2026-00123",
        issued_at="2026-08-18T08:00:00Z",
        expires_at="2026-08-20T18:00:00Z"
    )
    
    bytes1 = canonicalize_to_bytes(canonical1)
    bytes2 = canonicalize_to_bytes(canonical2)
    assert bytes1 == bytes2
    
    hash1 = calculate_content_hash(canonical1)
    hash2 = calculate_content_hash(canonical2)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex string

def test_ed25519_signing_and_verification():
    """Test 2 & 3: Signing and valid signature verification."""
    priv_key, pub_key = generate_keypair()
    pub_b64 = export_public_key_b64(pub_key)
    
    canonical = create_canonical_instruction(
        proof_id="PL-2026-00123",
        institution_id="POLICE-MP-001",
        action="PAYMENT",
        amount=80000,
        currency="INR",
        recipient="XXXX1234",
        purpose="CASE_SETTLEMENT",
        reference_id="CASE-2026-00123",
        issued_at="2026-08-18T08:00:00Z",
        expires_at="2026-08-20T18:00:00Z"
    )
    
    signature = sign_canonical_instruction(priv_key, canonical)
    assert isinstance(signature, str)
    
    # Valid verification
    is_valid = verify_ed25519_signature(pub_b64, signature, canonical)
    assert is_valid is True

def test_tamper_detection_modified_amount():
    """Test 4: Modified amount tamper detection."""
    priv_key, pub_key = generate_keypair()
    pub_b64 = export_public_key_b64(pub_key)
    
    canonical = create_canonical_instruction(
        proof_id="PL-2026-00123",
        institution_id="POLICE-MP-001",
        action="PAYMENT",
        amount=80000,
        currency="INR",
        recipient="XXXX1234",
        purpose="CASE_SETTLEMENT",
        reference_id="CASE-2026-00123",
        issued_at="2026-08-18T08:00:00Z",
        expires_at="2026-08-20T18:00:00Z"
    )
    
    original_hash = calculate_content_hash(canonical)
    signature = sign_canonical_instruction(priv_key, canonical)
    
    # Attacker changes amount from 80000 to 150000
    tampered = dict(canonical)
    tampered["amount"] = 150000
    
    tampered_hash = calculate_content_hash(tampered)
    assert original_hash != tampered_hash
    
    is_valid = verify_ed25519_signature(pub_b64, signature, tampered)
    assert is_valid is False

def test_tamper_detection_modified_recipient():
    """Test 5: Modified recipient tamper detection."""
    priv_key, pub_key = generate_keypair()
    pub_b64 = export_public_key_b64(pub_key)
    
    canonical = create_canonical_instruction(
        proof_id="PL-2026-00123",
        institution_id="POLICE-MP-001",
        action="PAYMENT",
        amount=80000,
        currency="INR",
        recipient="XXXX1234",
        purpose="CASE_SETTLEMENT",
        reference_id="CASE-2026-00123",
        issued_at="2026-08-18T08:00:00Z",
        expires_at="2026-08-20T18:00:00Z"
    )
    
    signature = sign_canonical_instruction(priv_key, canonical)
    
    # Attacker modifies recipient to fraudulent account
    tampered = dict(canonical)
    tampered["recipient"] = "ATTACKER_ACCOUNT_999"
    
    is_valid = verify_ed25519_signature(pub_b64, signature, tampered)
    assert is_valid is False

def test_invalid_signature_and_different_key():
    """Test 7: Signature from different keypair or corrupted signature fails."""
    priv_key1, pub_key1 = generate_keypair()
    priv_key2, pub_key2 = generate_keypair()
    pub_b64_2 = export_public_key_b64(pub_key2)
    
    canonical = create_canonical_instruction(
        proof_id="PL-2026-00123",
        institution_id="POLICE-MP-001",
        action="PAYMENT",
        amount=80000,
        currency="INR",
        recipient="XXXX1234",
        purpose="CASE_SETTLEMENT",
        reference_id="CASE-2026-00123",
        issued_at="2026-08-18T08:00:00Z",
        expires_at="2026-08-20T18:00:00Z"
    )
    
    signature_from_key1 = sign_canonical_instruction(priv_key1, canonical)
    
    # Verifying key1's signature with key2's public key must fail
    assert verify_ed25519_signature(pub_b64_2, signature_from_key1, canonical) is False
    
    # Corrupted signature string must fail safely
    corrupted_sig = signature_from_key1[:-4] + "AAAA"
    assert verify_ed25519_signature(pub_b64_2, corrupted_sig, canonical) is False
