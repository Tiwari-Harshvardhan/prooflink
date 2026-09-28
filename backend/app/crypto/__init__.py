"""
PROOFLINK Cryptographic Layer - QDS Edition

This package now implements teleportation-based Quantum Digital Signatures (QDS)
as a prototype/simulation, replacing the former Ed25519 classical signature scheme.

Exported symbols:
  - QDS signing/verification (primary, from qds.py via adapters)
  - Hashing utilities (SHA-256 fingerprint, canonicalization)
  - Ed25519 key utilities (backward-compatibility shim for Institution.public_key)

See app/crypto/qds.py for the full QDS protocol documentation.
"""

from app.crypto.keys import (
    generate_keypair,
    export_public_key_b64,
    export_private_key_b64,
    load_public_key_b64,
    load_private_key_b64,
)
from app.crypto.hashing import (
    create_canonical_instruction,
    canonicalize_to_bytes,
    calculate_content_hash,
)
from app.crypto.signing import sign_canonical_instruction
from app.crypto.verification import verify_ed25519_signature
from app.crypto.qds import (
    sign_instruction,
    verify_instruction,
    QDSSignatureRecord,
    QDSVerificationResult,
    PAULI_EIGENSTATES,
    PROTOCOL_VERSION,
    DEFAULT_SHOTS,
    DEFAULT_THRESHOLD,
    create_bell_pair,
    prepare_state,
    build_verification_circuit,
    calculate_error_rate,
    verify_against_threshold,
    register_signer,
    is_registered_signer,
)

__all__ = [
    # Ed25519 shims (backward compat — not used in QDS signing path)
    "generate_keypair",
    "export_public_key_b64",
    "export_private_key_b64",
    "load_public_key_b64",
    "load_private_key_b64",
    # Hashing / canonicalization (SHA-256 fingerprint, NOT the signature)
    "create_canonical_instruction",
    "canonicalize_to_bytes",
    "calculate_content_hash",
    # Signing/verification adapters (drop-in replacements)
    "sign_canonical_instruction",
    "verify_ed25519_signature",
    # QDS core (primary, new)
    "sign_instruction",
    "verify_instruction",
    "QDSSignatureRecord",
    "QDSVerificationResult",
    "PAULI_EIGENSTATES",
    "PROTOCOL_VERSION",
    "DEFAULT_SHOTS",
    "DEFAULT_THRESHOLD",
    "create_bell_pair",
    "prepare_state",
    "build_verification_circuit",
    "calculate_error_rate",
    "verify_against_threshold",
    "register_signer",
    "is_registered_signer",
]
