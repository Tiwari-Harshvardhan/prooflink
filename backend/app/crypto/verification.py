"""
Ed25519 Signature Verification for PROOFLINK Instructions.
"""
import base64
from typing import Union, Dict, Any
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature
from app.crypto.keys import load_public_key_b64
from app.crypto.hashing import canonicalize_to_bytes

def verify_ed25519_signature(
    public_key: Union[ed25519.Ed25519PublicKey, str],
    signature_b64: str,
    canonical_data: Union[Dict[str, Any], bytes]
) -> bool:
    """
    Verifies an Ed25519 signature against the canonical instruction bytes.
    Accepts public_key as either an Ed25519PublicKey object or a Base64 string.
    Returns True if valid, False otherwise.
    """
    try:
        if isinstance(public_key, str):
            pubkey_obj = load_public_key_b64(public_key)
        elif isinstance(public_key, ed25519.Ed25519PublicKey):
            pubkey_obj = public_key
        else:
            return False

        if isinstance(canonical_data, dict):
            message_bytes = canonicalize_to_bytes(canonical_data)
        elif isinstance(canonical_data, bytes):
            message_bytes = canonical_data
        else:
            return False

        signature_bytes = base64.b64decode(signature_b64.strip())
        pubkey_obj.verify(signature_bytes, message_bytes)
        return True
    except (InvalidSignature, ValueError, Exception):
        return False
