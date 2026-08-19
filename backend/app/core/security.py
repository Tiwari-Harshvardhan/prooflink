"""
Security and cryptographic hygiene invariants for PROOFLINK.
"""
import hmac
from typing import Any, Dict, Optional
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt
from fastapi import HTTPException, status

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = "prooflink-demo-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours


def constant_time_compare(val1: str, val2: str) -> bool:
    """Safely compare two strings in constant time to prevent timing attacks."""
    if not isinstance(val1, str) or not isinstance(val2, str):
        return False
    return hmac.compare_digest(val1.encode("utf-8"), val2.encode("utf-8"))


def sanitize_institution_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure private keys are never present in institution objects returned by API."""
    forbidden_keys = {"private_key", "secret", "private_key_raw", "privkey"}
    return {k: v for k, v in data.items() if k.lower() not in forbidden_keys}


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict:
    """Verify and decode a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
