from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime

class CreateProofLinkRequest(BaseModel):
    institution_id: str = Field(..., example="POLICE-MP-001")
    action: str = Field(..., example="PAYMENT")
    amount: float = Field(..., example=80000)
    currency: str = Field(default="INR", example="INR")
    recipient: str = Field(..., example="XXXX1234")
    purpose: str = Field(..., example="CASE_SETTLEMENT")
    reference_id: str = Field(..., example="CASE-2026-00123")
    instruction_id: Optional[str] = Field(default=None, example="abcd#1234")
    aadhaar_number: Optional[str] = Field(default=None, example="1234 5678 9012")
    phone_number: Optional[str] = Field(default=None, example="+91-9876543210")
    expires_at: datetime = Field(..., example="2026-08-20T18:00:00Z")

class CreateProofLinkResponse(BaseModel):
    proof_id: str = Field(..., example="PL-2026-00123")
    status: str = Field(..., example="ACTIVE")
    signature_status: str = Field(..., example="SIGNED")
    verification_url: str = Field(..., example="http://localhost:5173/verify/result/PL-2026-00123")
    qr_placeholder: bool = Field(default=True, example=True)

class RevokeRequest(BaseModel):
    reason: str = Field(..., example="Instruction cancelled")

class RevokeResponse(BaseModel):
    proof_id: str = Field(..., example="PL-2026-00123")
    status: str = Field(..., example="REVOKED")

class InstructionDetail(BaseModel):
    action: str
    amount: float
    currency: str
    recipient: str
    purpose: str
    reference_id: str

class InstitutionDetail(BaseModel):
    id: str
    name: str
    type: Optional[str] = None
    public_key: Optional[str] = None
    status: Optional[str] = None

class ProofLinkDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    proof_id: str
    institution: InstitutionDetail
    instruction: InstructionDetail
    content_hash: str
    signature: str
    status: str
    created_at: datetime
    expires_at: datetime
