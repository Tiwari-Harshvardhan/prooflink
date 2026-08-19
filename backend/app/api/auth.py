"""
Authentication API endpoints: login, register, OTP verification.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.database.connection import get_db
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    CitizenRegisterRequest,
    CitizenRegisterResponse,
    OfficialRegisterRequest,
    OfficialRegisterResponse,
    OTPRequest,
    OTPResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
    CurrentUserResponse,
)
from app.services.auth_service import (
    register_citizen,
    register_official,
    login_user,
    generate_and_send_otp,
    verify_otp,
    get_user_by_id,
    get_citizen_by_user_id,
    get_official_by_user_id,
)
from app.core.security import create_access_token, verify_access_token


router = APIRouter(prefix="/auth", tags=["Auth"])


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Dependency to get current user from JWT token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )

    payload = verify_access_token(token)
    user_id = payload.get("sub")
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user


@router.post("/citizen/register", response_model=CitizenRegisterResponse, status_code=status.HTTP_201_CREATED)
def register_citizen_endpoint(
    request: CitizenRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new citizen with phone, password, and KYC verification.
    """
    user, citizen = register_citizen(db, request)
    return CitizenRegisterResponse(
        user_id=user.id,
        name=user.name,
        phone=user.phone,
        kyc_status=citizen.kyc_status,
        message="Citizen registered successfully. Please verify OTP to complete registration."
    )


@router.post("/official/register", response_model=OfficialRegisterResponse, status_code=status.HTTP_201_CREATED)
def register_official_endpoint(
    request: OfficialRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new official with phone, password, and institution.
    """
    user, official = register_official(db, request)
    return OfficialRegisterResponse(
        user_id=user.id,
        name=user.name,
        phone=user.phone,
        institution_id=official.institution_id,
        message="Official registered successfully."
    )


@router.post("/login", response_model=TokenResponse)
def login_endpoint(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with phone and password.
    Returns JWT access token and user info.
    """
    user = login_user(db, request.phone, request.password)

    # If citizen, they still need OTP verification before full access
    citizen = get_citizen_by_user_id(db, user.id)
    if citizen and not citizen.phone_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your OTP first."
        )

    access_token = create_access_token(
        data={"sub": user.id, "phone": user.phone, "role": user.role}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        role=user.role
    )


@router.post("/citizen/send-otp", response_model=OTPResponse)
def send_otp_endpoint(
    request: OTPRequest,
    db: Session = Depends(get_db)
):
    """
    Send OTP to citizen's phone for verification.
    """
    otp = generate_and_send_otp(db, request.phone)
    return OTPResponse(
        status="sent",
        message="OTP sent successfully to your phone.",
        phone=request.phone
    )


@router.post("/citizen/verify-otp", response_model=OTPVerifyResponse)
def verify_otp_endpoint(
    request: OTPVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verify OTP sent to citizen's phone.
    """
    success, access_token = verify_otp(db, request.phone, request.otp)
    if success:
        return OTPVerifyResponse(
            status="verified",
            message="OTP verified successfully.",
            access_token=access_token,
            token_type="bearer"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP verification failed."
        )


@router.get("/me", response_model=CurrentUserResponse)
def get_current_user_endpoint(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user's info.
    """
    return CurrentUserResponse(
        user_id=current_user.id,
        name=current_user.name,
        phone=current_user.phone,
        role=current_user.role,
        email=current_user.email
    )
