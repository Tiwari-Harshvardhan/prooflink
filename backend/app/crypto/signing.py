"""
Ed25519 Digital Signing for PROOFLINK Instructions.
"""
import base64
from typing import Union, Dict, Any
from cryptography.hazmat.primitives.asymmetric import ed25519
from app.crypto.hashing import canonicalize_to_bytes

def sign_canonical_instruction(
    private_key: ed25519.Ed25519PrivateKey,
    canonical_data: Union[Dict[str, Any], bytes]
) -> str:
    """
    Signs the canonical instruction bytes using the institution's Ed25519 private key.
    Returns the base64-encoded signature.
    """
    if isinstance(canonical_data, dict):
        message_bytes = canonicalize_to_bytes(canonical_data)
    elif isinstance(canonical_data, bytes):
        message_bytes = canonical_data
    else:
        raise TypeError(f"Invalid canonical data type: {type(canonical_data)}")
        
    signature_bytes = private_key.sign(message_bytes)
    return base64.b64encode(signature_bytes).decode("utf-8")
