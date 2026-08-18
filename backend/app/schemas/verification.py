from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.schemas.prooflink import InstructionDetail, InstitutionDetail

class VerifyRequest(BaseModel):
    proof_id: str = Field(..., example="PL-2026-00123")

class VerificationChecks(BaseModel):
    exists: bool = Field(..., description="ProofLink exists in database")
    institution_recognized: bool = Field(..., description="Institution is registered and active")
    signature_valid: bool = Field(..., description="Ed25519 digital signature verified against institution public key")
    hash_valid: bool = Field(..., description="SHA-256 canonical hash matches stored fingerprint")
    amount_match: bool = Field(..., description="Instruction amount integrity intact")
    recipient_match: bool = Field(..., description="Recipient integrity intact")
    not_expired: bool = Field(..., description="Instruction has not passed expiration timestamp")
    not_revoked: bool = Field(..., description="Instruction has not been revoked")

class VerifyResponse(BaseModel):
    status: str = Field(..., example="VERIFIED", description="One of: VERIFIED, NOT_FOUND, MISMATCH, INVALID_SIGNATURE, HASH_MISMATCH, EXPIRED, REVOKED")
    proof_id: str = Field(..., example="PL-2026-00123")
    institution: Optional[InstitutionDetail] = None
    instruction: Optional[InstructionDetail] = None
    checks: VerificationChecks
    message: Optional[str] = None
