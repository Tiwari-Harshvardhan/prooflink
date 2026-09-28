"""
Key management compatibility shim for PROOFLINK.

The QDS prototype does NOT use Ed25519 keys for signing/verification.
The functions in this module are PRESERVED for backward compatibility:

  - institution_service.py still calls generate_keypair(),
    export_public_key_b64(), etc. to populate the institutions.public_key
    column (a database schema field that cannot be dropped without a
    migration).

  - The Institution.public_key column is now effectively a placeholder:
    its value is still set during seeding but is NOT used for QDS
    signature verification.

The actual QDS signing/verification is handled entirely within
app/crypto/qds.py using Pauli eigenstates and quantum teleportation.

Legacy Ed25519 functions are kept to avoid breaking:
  - institution seeding (institution_service.py)
  - any integration test that inspects the public_key field
  - the /api/v1/institutions endpoint (returns public_key in response)

In a production migration you would drop or repurpose the public_key
column. For this prototype, we leave it in place.
"""

import base64
import hashlib
from typing import Tuple

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


def generate_keypair() -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
    """
    Generate a new Ed25519 keypair.

    NOTE: In the QDS prototype these keys are used ONLY as a placeholder
    for the Institution.public_key database column. They are NOT used in
    the QDS signing or verification path.
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key


def export_public_key_b64(public_key: ed25519.Ed25519PublicKey) -> str:
    """Export public key to base64 raw 32-byte representation."""
    raw_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return base64.b64encode(raw_bytes).decode("utf-8")


def export_private_key_b64(private_key: ed25519.Ed25519PrivateKey) -> str:
    """Export private key to base64 raw 32-byte representation."""
    raw_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    return base64.b64encode(raw_bytes).decode("utf-8")


def load_public_key_b64(public_key_b64: str) -> ed25519.Ed25519PublicKey:
    """Load an Ed25519 public key from a base64 encoded raw 32-byte string."""
    raw_bytes = base64.b64decode(public_key_b64.strip())
    if len(raw_bytes) != 32:
        raise ValueError(
            f"Invalid Ed25519 public key length: {len(raw_bytes)} bytes (expected 32)"
        )
    return ed25519.Ed25519PublicKey.from_public_bytes(raw_bytes)


def load_private_key_b64(private_key_b64: str) -> ed25519.Ed25519PrivateKey:
    """Load an Ed25519 private key from a base64 encoded raw 32-byte string."""
    raw_bytes = base64.b64decode(private_key_b64.strip())
    if len(raw_bytes) != 32:
        raise ValueError(
            f"Invalid Ed25519 private key length: {len(raw_bytes)} bytes (expected 32)"
        )
    return ed25519.Ed25519PrivateKey.from_private_bytes(raw_bytes)
