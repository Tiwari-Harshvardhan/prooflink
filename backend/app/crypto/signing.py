"""
QDS Signing Adapter for PROOFLINK Instructions.

This module REPLACES the former Ed25519-based signing with a
teleportation-based Quantum Digital Signature (QDS) prototype/simulation.

Public API is unchanged:
    sign_canonical_instruction(private_key, canonical_data) -> str

The private_key argument is now IGNORED (it was an Ed25519 key object).
The signer identity is now derived from the canonical_data["institution_id"]
field, which is always present in PROOFLINK canonical instructions.

The returned string is a JSON-serialized QDSSignatureRecord instead of
a base64 Ed25519 signature.  The ProofLink.signature (Text) column
accommodates this transparently because it stores arbitrary text.

NOTE: This is a prototype/simulation. See app/crypto/qds.py for details.
"""

from typing import Union, Dict, Any

from app.crypto.hashing import canonicalize_to_bytes  # kept for any callers that use it
from app.crypto.qds import sign_instruction as _qds_sign_instruction


def sign_canonical_instruction(
    private_key: Any,  # Kept for API compatibility; not used in QDS path
    canonical_data: Union[Dict[str, Any], bytes],
) -> str:
    """
    Sign a canonical instruction using the teleportation-based QDS prototype.

    Replaces the former Ed25519 signing.  The private_key parameter is
    accepted but not used — the QDS protocol derives signer identity
    from the institution_id embedded in canonical_data.

    Args:
        private_key: Ignored (kept for drop-in API compatibility).
        canonical_data: Canonical instruction dict OR bytes.
                        Must contain "institution_id" and "proof_id" keys
                        when supplied as a dict.

    Returns:
        JSON string representation of QDSSignatureRecord.
        This replaces the former base64 Ed25519 signature string.

    Raises:
        TypeError: If canonical_data is neither a dict nor bytes.
        KeyError:  If canonical_data dict is missing required fields.
    """
    if isinstance(canonical_data, bytes):
        import json
        canonical_dict: Dict[str, Any] = json.loads(canonical_data.decode("utf-8"))
    elif isinstance(canonical_data, dict):
        canonical_dict = canonical_data
    else:
        raise TypeError(
            f"canonical_data must be dict or bytes, got {type(canonical_data)}"
        )

    institution_id: str = canonical_dict["institution_id"]
    proof_id: str = canonical_dict["proof_id"]

    record = _qds_sign_instruction(
        canonical_data=canonical_dict,
        institution_id=institution_id,
        proof_id=proof_id,
    )
    return record.to_json()
