"""
Authentication and authorization schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Request to login with phone and password."""
    phone: str = Field(..., example="+91-9876543210")
    password: str = Field(..., example="password123")


class TokenResponse(BaseModel):
    """JWT token response after successful login."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


class CitizenRegisterRequest(BaseModel):
    """Request to register as a citizen with KYC."""
    name: str = Field(..., example="Rajesh Kumar")
    phone: str = Field(..., example="+91-9876543210")
    password: str = Field(..., example="password123")
    aadhaar_number: str = Field(..., example="1234 5678 9012")


class CitizenRegisterResponse(BaseModel):
    """Response after citizen registration."""
    user_id: str
    name: str
    phone: str
    kyc_status: str
    message: str


class OTPRequest(BaseModel):
    """Request to send OTP."""
    phone: str = Field(..., example="+91-9876543210")


class OTPResponse(BaseModel):
    """Response after sending OTP."""
    status: str
    message: str
    phone: str


class OTPVerifyRequest(BaseModel):
    """Request to verify OTP."""
    phone: str = Field(..., example="+91-9876543210")
    otp: str = Field(..., example="123456")


class OTPVerifyResponse(BaseModel):
    """Response after verifying OTP."""
    status: str
    message: str
    access_token: Optional[str] = None
    token_type: Optional[str] = None


class OfficialRegisterRequest(BaseModel):
    """Request to register as an official."""
    name: str = Field(..., example="Sharma Official")
    phone: str = Field(..., example="+91-9876543211")
    password: str = Field(..., example="password123")
    institution_id: str = Field(..., example="POLICE-MP-001")
    official_id: str = Field(..., example="OFF-001")


class OfficialRegisterResponse(BaseModel):
    """Response after official registration."""
    user_id: str
    name: str
    phone: str
    institution_id: str
    message: str


class CurrentUserResponse(BaseModel):
    """Response for current user info."""
    user_id: str
    name: str
    phone: str
    role: str
    email: Optional[str] = None
