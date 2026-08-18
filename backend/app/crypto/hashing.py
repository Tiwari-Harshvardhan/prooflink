"""
Canonical instruction construction and SHA-256 hashing.
"""
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, Union

def format_iso_timestamp(dt: Union[datetime, str]) -> str:
    """Format any datetime or timestamp string to standard ISO UTC (YYYY-MM-DDTHH:MM:SSZ)."""
    if isinstance(dt, str):
        clean_str = dt.strip().replace(" ", "T")
        try:
            dt = datetime.fromisoformat(clean_str.replace("Z", "+00:00"))
        except Exception:
            return clean_str
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        # Format without microseconds for deterministic canonical representation
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(dt)

def create_canonical_instruction(
    proof_id: str,
    institution_id: str,
    action: str,
    amount: Union[int, float],
    currency: str,
    recipient: str,
    purpose: str,
    reference_id: str,
    issued_at: Union[datetime, str],
    expires_at: Union[datetime, str]
) -> Dict[str, Any]:
    """
    Construct a standardized dictionary representation of the instruction.
    All keys are lowercase standard names.
    """
    return {
        "action": action.strip().upper(),
        "amount": float(amount),
        "currency": currency.strip().upper(),
        "expires_at": format_iso_timestamp(expires_at),
        "institution_id": institution_id.strip(),
        "issued_at": format_iso_timestamp(issued_at),
        "proof_id": proof_id.strip(),
        "purpose": purpose.strip(),
        "recipient": recipient.strip(),
        "reference_id": reference_id.strip(),
    }

def canonicalize_to_bytes(canonical_dict: Dict[str, Any]) -> bytes:
    """
    Convert canonical instruction dictionary to deterministic byte sequence
    using sorted keys and compact JSON separators.
    """
    canonical_json = json.dumps(canonical_dict, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return canonical_json.encode("utf-8")

def calculate_content_hash(data: Union[Dict[str, Any], bytes, str]) -> str:
    """
    Compute SHA-256 hex digest of the canonical instruction representation.
    """
    if isinstance(data, dict):
        byte_data = canonicalize_to_bytes(data)
    elif isinstance(data, str):
        byte_data = data.encode("utf-8")
    elif isinstance(data, bytes):
        byte_data = data
    else:
        raise TypeError(f"Unsupported data type for hashing: {type(data)}")
    
    return hashlib.sha256(byte_data).hexdigest()
