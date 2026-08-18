// TypeScript interfaces mirroring the backend SQLAlchemy schemas.
// Keep these in sync with database/models.py and the FastAPI response models.

export type InstitutionType =
  | 'POLICE'
  | 'BANK'
  | 'GOVERNMENT'
  | 'COURT'
  | 'TELECOM'
  | 'OTHER'

export type InstitutionStatus = 'ACTIVE' | 'SUSPENDED'

export interface Institution {
  id: number
  institution_id: string
  name: string
  type: InstitutionType
  // Public key only. Private keys never leave the backend/crypto layer.
  public_key: string
  status: InstitutionStatus
  created_at: string
}

export type ProofLinkStatus = 'ACTIVE' | 'EXPIRED' | 'REVOKED'

export interface ProofLink {
  id: number
  proof_id: string
  institution_id: string
  action: string
  amount: string
  currency: string
  recipient: string
  purpose: string
  reference_id: string
  issued_at: string
  expires_at: string
  // Signature and content_hash are produced by the backend/crypto layer.
  signature: string
  content_hash: string
  status: ProofLinkStatus
  created_at: string
}

export interface Revocation {
  id: number
  proof_id: string
  reason: string
  revoked_at: string
  revoked_by: string
}

export interface CreateProofLinkRequest {
  action: string
  amount: string
  currency: string
  recipient: string
  purpose: string
  reference_id: string
  expires_at: string
}

export interface CreateProofLinkResponse {
  proof_id: string
  verification_url: string
  status: ProofLinkStatus
  qr_placeholder: true
}

export interface RevokeProofLinkRequest {
  reason: string
  revoked_by: string
}

export type VerificationResult =
  | 'VERIFIED'
  | 'NOT_FOUND'
  | 'MISMATCH'
  | 'INVALID_SIGNATURE'
  | 'EXPIRED'
  | 'REVOKED'

export interface VerificationChecks {
  prooflink_exists: boolean
  institution_recognized: boolean
  signature_valid: boolean
  instruction_matches: boolean
  amount_matches: boolean
  recipient_matches: boolean
  not_expired: boolean
  not_revoked: boolean
}

export interface VerifyRequest {
  proof_id: string
}

export interface VerifyResponse {
  result: VerificationResult
  proof_id: string
  checks: VerificationChecks
  institution?: {
    institution_id: string
    name: string
    type: InstitutionType
  }
  prooflink?: {
    action: string
    amount: string
    currency: string
    recipient: string
    purpose: string
    reference_id: string
    issued_at: string
    expires_at: string
    signature_status: 'VALID' | 'INVALID'
    instruction_status: ProofLinkStatus
    revocation_status: 'NOT_REVOKED' | 'REVOKED'
  }
  message: string
}

export interface InstitutionStats {
  total: number
  active: number
  expired: number
  revoked: number
}

export interface HealthResponse {
  status: 'ok'
  version: string
}
