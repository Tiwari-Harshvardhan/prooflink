"""
Security and cryptographic hygiene invariants for PROOFLINK.
"""
import hmac
from typing import Any, Dict

def constant_time_compare(val1: str, val2: str) -> bool:
    """Safely compare two strings in constant time to prevent timing attacks."""
    if not isinstance(val1, str) or not isinstance(val2, str):
        return False
    return hmac.compare_digest(val1.encode("utf-8"), val2.encode("utf-8"))

def sanitize_institution_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure private keys are never present in institution objects returned by API."""
    forbidden_keys = {"private_key", "secret", "private_key_raw", "privkey"}
    return {k: v for k, v in data.items() if k.lower() not in forbidden_keys}
