"""
QDS Verification Adapter for PROOFLINK Instructions.

This module REPLACES the former Ed25519-based signature verification with a
teleportation-based Quantum Digital Signature (QDS) prototype/simulation.

Public API maintained for backward compatibility:
    verify_ed25519_signature(public_key, signature_b64, canonical_data) -> bool

The public_key argument is now IGNORED.
The signature_b64 argument now contains the JSON string of a QDSSignatureRecord
(stored in the ProofLink.signature Text column).

NOTE: This is a prototype/simulation. See app/crypto/qds.py for full details.
"""

from typing import Union, Dict, Any

from app.crypto.qds import (
    verify_instruction as _qds_verify,
    QDSVerificationResult,
    DEFAULT_SHOTS,
    DEFAULT_THRESHOLD,
)


def verify_ed25519_signature(
    public_key: Any,  # Kept for API compatibility; not used in QDS path
    signature_b64: str,  # Now holds QDSSignatureRecord JSON
    canonical_data: Union[Dict[str, Any], bytes],
    shots: int = DEFAULT_SHOTS,
    threshold: float = DEFAULT_THRESHOLD,
    allow_reverify: bool = True,
) -> bool:
    """
    Verify a QDS signature (drop-in replacement for Ed25519 verification).

    Returns True if the QDS verification passes (VERIFIED), False otherwise.

    Args:
        public_key:    Ignored (kept for API compatibility).
        signature_b64: JSON string of QDSSignatureRecord (stored in ProofLink.signature).
        canonical_data: Canonical instruction dict or bytes.
        shots:         Number of Qiskit measurement shots.
        threshold:     Statistical acceptance threshold.

    Returns:
        True if status == "VERIFIED", False for any other status.
    """
    if isinstance(canonical_data, bytes):
        import json
        canonical_dict: Dict[str, Any] = json.loads(canonical_data.decode("utf-8"))
    elif isinstance(canonical_data, dict):
        canonical_dict = canonical_data
    else:
        return False

    try:
        institution_id: str = canonical_dict.get("institution_id", "")
        result: QDSVerificationResult = _qds_verify(
            canonical_data=canonical_dict,
            signature_json=signature_b64,
            institution_id=institution_id,
            shots=shots,
            threshold=threshold,
            allow_reverify=allow_reverify,
        )
        return result.status == "VERIFIED"
    except Exception:
        return False


def verify_qds_signature_full(
    signature_json: str,
    canonical_data: Dict[str, Any],
    institution_id: str,
    shots: int = DEFAULT_SHOTS,
    threshold: float = DEFAULT_THRESHOLD,
    simulate_forgery: bool = False,
    simulate_channel_noise: bool = False,
    channel_noise_type: str = "X",
    allow_reverify: bool = True,
) -> QDSVerificationResult:
    """
    Full QDS verification — returns the complete QDSVerificationResult.

    Use this in verification_service.py to access quantum measurement
    statistics (shots, error_rate, etc.) for the verification response.

    Args:
        signature_json:       QDSSignatureRecord JSON from ProofLink.signature.
        canonical_data:       Canonical instruction dict.
        institution_id:       Institution/signer ID.
        shots:                Measurement shots.
        threshold:            Statistical acceptance threshold.
        simulate_forgery:     Demo: inject forgery simulation.
        simulate_channel_noise: Demo: inject channel noise.
        channel_noise_type:   Noise type: "X", "Y", or "Z".
        allow_reverify:       Allow re-checking an existing persistent instruction (default True).

    Returns:
        QDSVerificationResult with full statistics.
    """
    return _qds_verify(
        canonical_data=canonical_data,
        signature_json=signature_json,
        institution_id=institution_id,
        shots=shots,
        threshold=threshold,
        simulate_forgery=simulate_forgery,
        simulate_channel_noise=simulate_channel_noise,
        channel_noise_type=channel_noise_type,
        allow_reverify=allow_reverify,
    )
