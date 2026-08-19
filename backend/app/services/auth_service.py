"""
Authentication service: user registration, login, and KYC flows.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
import uuid
import random
import hashlib
import re
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.citizen import Citizen
from app.models.official import Official
from app.models.otp import OTP
from app.schemas.auth import (
    CitizenRegisterRequest,
    OfficialRegisterRequest,
)
from app.services.kyc.kyc_service import get_kyc_service
from app.services.sms.sms_service import get_sms_service
from app.core.security import hash_password, verify_password, create_access_token


def normalize_phone(phone: str) -> str:
    """
    Normalizes any phone format (+91 7489463399, 7489463399, +91-7489-463399, 07489463399)
    to standard E.164 (+917489463399).
    """
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 10:
        return f"+91{digits}"
    elif len(digits) == 11 and digits.startswith("0"):
        return f"+91{digits[1:]}"
    elif len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"
    elif digits:
        return f"+{digits}"
    return ""


def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
    """Retrieve user by phone number (handles both normalized and formatted inputs)."""
    norm = normalize_phone(phone)
    return db.query(User).filter((User.phone == norm) | (User.phone == phone)).first()


def aadhaar_hash(aadhaar: str) -> str:
    normalized = re.sub(r"\D", "", aadhaar or "")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Retrieve user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_citizen_by_user_id(db: Session, user_id: str) -> Optional[Citizen]:
    """Retrieve citizen by user ID."""
    return db.query(Citizen).filter(Citizen.user_id == user_id).first()


def get_official_by_user_id(db: Session, user_id: str) -> Optional[Official]:
    """Retrieve official by user ID."""
    return db.query(Official).filter(Official.user_id == user_id).first()


def register_citizen(db: Session, request: CitizenRegisterRequest) -> Tuple[User, Citizen]:
    """
    Register a new citizen with phone, password, and KYC.
    1. Verify phone not already registered
    2. Run KYC verification
    3. Create user and citizen records
    4. Return user and citizen
    """
    # Check if phone already registered
    request.phone = normalize_phone(request.phone)
    existing_user = get_user_by_phone(db, request.phone)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phone number {request.phone} is already registered."
        )

    # Run KYC verification
    kyc_service = get_kyc_service()
    kyc_result = kyc_service.verify_identity(
        full_name=request.name,
        aadhaar_number=request.aadhaar_number,
        phone_number=request.phone
    )

    if kyc_result.get("status") != "VERIFIED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="KYC verification failed. Please try again."
        )

    # Create user
    user_id = f"USER-{uuid.uuid4().hex[:12].upper()}"
    user = User(
        id=user_id,
        name=request.name,
        phone=request.phone,
        email=None,
        password_hash=hash_password(request.password),
        role="CITIZEN",
        status="ACTIVE"
    )
    db.add(user)
    db.flush()

    # Create citizen record
    citizen_id = f"CITIZEN-{uuid.uuid4().hex[:12].upper()}"
    citizen = Citizen(
        id=citizen_id,
        user_id=user_id,
        aadhaar_reference=kyc_result.get("aadhaar_reference", ""),
        aadhaar_hash=aadhaar_hash(request.aadhaar_number),
        masked_aadhaar=kyc_result.get("masked_aadhaar", ""),
        kyc_status="VERIFIED",
        phone_verified=False
    )
    db.add(citizen)
    db.commit()
    db.refresh(user)
    db.refresh(citizen)

    # Automatically generate and dispatch the initial verification OTP
    generate_and_send_otp(db, user.phone)

    return user, citizen


def register_official(db: Session, request: OfficialRegisterRequest) -> Tuple[User, Official]:
    """
    Register a new official with phone, password, and institution.
    1. Verify phone not already registered
    2. Create user and official records
    3. Return user and official
    """
    from app.services.institution_service import get_institution

    # Check if phone already registered
    request.phone = normalize_phone(request.phone)
    existing_user = get_user_by_phone(db, request.phone)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phone number {request.phone} is already registered."
        )

    # Verify institution exists
    institution = get_institution(db, request.institution_id)
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Institution '{request.institution_id}' not found."
        )

    # Create user
    user_id = f"USER-{uuid.uuid4().hex[:12].upper()}"
    user = User(
        id=user_id,
        name=request.name,
        phone=request.phone,
        email=None,
        password_hash=hash_password(request.password),
        role="OFFICIAL",
        status="ACTIVE"
    )
    db.add(user)
    db.flush()

    # Create official record
    official_id = f"OFFICIAL-{uuid.uuid4().hex[:12].upper()}"
    official = Official(
        id=official_id,
        user_id=user_id,
        institution_id=request.institution_id,
        official_id=request.official_id
    )
    db.add(official)
    db.commit()
    db.refresh(user)
    db.refresh(official)

    return user, official


def login_user(db: Session, phone: str, password: str) -> User:
    """
    Login user with phone and password.
    1. Find user by phone
    2. Verify password
    3. Return user if valid
    """
    user = get_user_by_phone(db, phone)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone or password."
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone or password."
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active."
        )

    return user


def generate_and_send_otp(db: Session, phone: str) -> OTP:
    """
    Generate and send OTP to a phone number for citizen verification.
    1. Find or create OTP record
    2. Generate 6-digit OTP
    3. Hash and store OTP
    4. Send via SMS
    5. Return OTP record
    """
    user = get_user_by_phone(db, phone)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Generate 6-digit OTP
    otp_code = f"{random.randint(100000, 999999)}"
    otp_hash = hashlib.sha256(otp_code.encode("utf-8")).hexdigest()

    # Delete existing OTPs for this user
    db.query(OTP).filter(OTP.user_id == user.id).delete()

    # Create new OTP record
    otp_id = f"OTP-{uuid.uuid4().hex[:12].upper()}"
    otp = OTP(
        id=otp_id,
        user_id=user.id,
        phone=phone,
        otp_hash=otp_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        attempts=0
    )
    db.add(otp)
    db.commit()
    db.refresh(otp)

    # Send OTP via SMS
    sms_service = get_sms_service()
    sms_service.send_sms(
        phone_number=phone,
        message=f"Your PROOFLINK verification code is: {otp_code}. Valid for 10 minutes."
    )

    return otp


def verify_otp(db: Session, phone: str, otp_code: str) -> Tuple[bool, Optional[str]]:
    """
    Verify OTP for a phone number.
    1. Find user
    2. In development mode, allow universal test code 123456
    3. Verify OTP hash against stored record
    4. Mark citizen phone as verified
    5. Return (success, access_token)
    """
    from app.core.config import settings

    user = get_user_by_phone(db, phone)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # In development / mock mode, allow universal demo OTP "123456"
    is_dev_demo = (settings.ENVIRONMENT == "development" or settings.SMS_PROVIDER == "mock") and otp_code == "123456"

    otp = db.query(OTP).filter(OTP.user_id == user.id).order_by(OTP.created_at.desc()).first()

    if not is_dev_demo:
        if not otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No OTP found. Please request a new one."
            )

        # Check if expired
        expires_at = otp.expires_at if otp.expires_at.tzinfo else otp.expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired. Please request a new one."
            )

        # Check attempt limit
        if otp.attempts >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many failed attempts. Please request a new OTP."
            )

        # Verify OTP hash
        otp_hash = hashlib.sha256(otp_code.encode("utf-8")).hexdigest()
        if otp_hash != otp.otp_hash:
            otp.attempts += 1
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP. Please try again."
            )

    # Mark as verified
    if otp:
        otp.verified_at = datetime.now(timezone.utc)
        db.commit()

    # Mark citizen phone as verified
    citizen = get_citizen_by_user_id(db, user.id)
    if citizen:
        citizen.phone_verified = True
        db.commit()

    # Create access token
    access_token = create_access_token(
        data={"sub": user.id, "phone": user.phone, "role": user.role}
    )

    return True, access_token
