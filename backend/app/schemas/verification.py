from pydantic import BaseModel, Field, ConfigDict, model_validator
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any
from app.schemas.prooflink import InstructionDetail, InstitutionDetail

class VerifyRequest(BaseModel):
    prooflink: str | None = Field(default=None, example="PLTOKEN123")
    proof_id: str | None = Field(default=None, description="Legacy alias")

    @model_validator(mode="after")
    def extract_token(self):
        value = (self.prooflink or self.proof_id or "").strip()
        if not value:
            raise ValueError("A ProofLink token is required.")
        if "://" in value:
            parsed = urlparse(value)
            value = parse_qs(parsed.query).get("token", [""])[0]
        if not value:
            raise ValueError("The supplied ProofLink URL does not contain a token.")
        self.prooflink = value
        return self

class VerificationChecks(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    exists: bool = Field(..., description="ProofLink exists in database")
    institution_recognized: bool = Field(..., description="Institution is registered and active")
    signature_valid: bool = Field(..., description="Ed25519 digital signature verified against institution public key")
    hash_valid: bool = Field(..., description="SHA-256 canonical hash matches stored fingerprint")
    amount_match: bool = Field(..., description="Instruction amount integrity intact")
    recipient_match: bool = Field(..., description="Recipient integrity intact")
    not_expired: bool = Field(..., description="Instruction has not passed expiration timestamp")
    not_revoked: bool = Field(..., description="Instruction has not been revoked")

    prooflink_exists: bool = Field(default=False, description="Frontend-compatible alias for exists")
    amount_matches: bool = Field(default=False, description="Frontend-compatible alias for amount_match")
    recipient_matches: bool = Field(default=False, description="Frontend-compatible alias for recipient_match")

    @model_validator(mode="after")
    def sync_alias_fields(self):
        self.prooflink_exists = self.exists
        self.amount_matches = self.amount_match
        self.recipient_matches = self.recipient_match
        return self

class VerifyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: Optional[str] = Field(default=None, example="VERIFIED", description="Legacy status field")
    result: Optional[str] = Field(default=None, example="VERIFIED", description="Frontend-friendly verification result")
    proof_id: str = Field(..., example="PL-2026-00123")
    institution: Optional[InstitutionDetail] = None
    instruction: Optional[InstructionDetail] = None
    checks: VerificationChecks
    message: Optional[str] = None
    prooflink: Optional[Dict[str, Any]] = None
