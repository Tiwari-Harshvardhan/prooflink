// In-memory mock data used until the FastAPI backend is available.
// Nothing here performs real verification or cryptography — it only
// simulates the shapes the real API will return.

import type {
  Institution,
  ProofLink,
  VerifyResponse,
  InstitutionStats,
} from '@/types'

export const mockInstitutions: Institution[] = [
  {
    id: 1,
    institution_id: 'INST-POLICE-MH-014',
    name: 'Maharashtra Police — Cyber Cell',
    type: 'POLICE',
    public_key: 'ed25519:8f3a...c21e',
    status: 'ACTIVE',
    created_at: '2025-11-02T09:00:00Z',
  },
  {
    id: 2,
    institution_id: 'INST-BANK-HDFC-001',
    name: 'HDFC Bank Ltd.',
    type: 'BANK',
    public_key: 'ed25519:2b91...77aa',
    status: 'ACTIVE',
    created_at: '2025-10-14T09:00:00Z',
  },
]

export const mockProofLinks: ProofLink[] = [
  {
    id: 101,
    proof_id: 'PL-2026-00123',
    institution_id: 'INST-POLICE-MH-014',
    action: 'FUND_TRANSFER',
    amount: '80000.00',
    currency: 'INR',
    recipient: 'Case Escrow Account #4471',
    purpose: 'Fraud investigation escrow hold',
    reference_id: 'FIR-2026-778812',
    issued_at: '2026-08-10T10:15:00Z',
    expires_at: '2026-08-20T10:15:00Z',
    signature: 'ed25519_sig:9f1c...4b7e',
    content_hash: 'sha256:71a3...e90c',
    status: 'ACTIVE',
    created_at: '2026-08-10T10:15:00Z',
  },
  {
    id: 102,
    proof_id: 'PL-2026-00098',
    institution_id: 'INST-BANK-HDFC-001',
    action: 'KYC_VERIFICATION_CALL',
    amount: '0.00',
    currency: 'INR',
    recipient: 'N/A',
    purpose: 'Scheduled KYC re-verification call',
    reference_id: 'KYC-REQ-55231',
    issued_at: '2026-07-28T12:00:00Z',
    expires_at: '2026-08-04T12:00:00Z',
    signature: 'ed25519_sig:aa02...11d8',
    content_hash: 'sha256:44bb...920f',
    status: 'EXPIRED',
    created_at: '2026-07-28T12:00:00Z',
  },
  {
    id: 103,
    proof_id: 'PL-2026-00071',
    institution_id: 'INST-BANK-HDFC-001',
    action: 'FUND_TRANSFER',
    amount: '150000.00',
    currency: 'INR',
    recipient: 'Suspicious External Account',
    purpose: 'Revoked after internal review',
    reference_id: 'TXN-REQ-11029',
    issued_at: '2026-07-15T08:30:00Z',
    expires_at: '2026-07-25T08:30:00Z',
    signature: 'ed25519_sig:5c67...2f01',
    content_hash: 'sha256:0912...bbaa',
    status: 'REVOKED',
    created_at: '2026-07-15T08:30:00Z',
  },
]

export function mockStatsFor(institutionId: string): InstitutionStats {
  const links = mockProofLinks.filter((p) => p.institution_id === institutionId)
  return {
    total: links.length,
    active: links.filter((p) => p.status === 'ACTIVE').length,
    expired: links.filter((p) => p.status === 'EXPIRED').length,
    revoked: links.filter((p) => p.status === 'REVOKED').length,
  }
}

export function mockVerify(proofId: string): VerifyResponse {
  const link = mockProofLinks.find((p) => p.proof_id === proofId.trim())

  if (!link) {
    return {
      result: 'NOT_FOUND',
      proof_id: proofId,
      checks: {
        prooflink_exists: false,
        institution_recognized: false,
        signature_valid: false,
        instruction_matches: false,
        amount_matches: false,
        recipient_matches: false,
        not_expired: false,
        not_revoked: false,
      },
      message: 'No ProofLink exists with this ID in the authoritative registry.',
    }
  }

  const institution = mockInstitutions.find((i) => i.institution_id === link.institution_id)
  const now = new Date()
  const notExpired = new Date(link.expires_at) > now
  const notRevoked = link.status !== 'REVOKED'

  let result: VerifyResponse['result'] = 'VERIFIED'
  if (link.status === 'REVOKED') result = 'REVOKED'
  else if (!notExpired) result = 'EXPIRED'

  return {
    result,
    proof_id: link.proof_id,
    checks: {
      prooflink_exists: true,
      institution_recognized: !!institution,
      signature_valid: true,
      instruction_matches: true,
      amount_matches: true,
      recipient_matches: true,
      not_expired: notExpired,
      not_revoked: notRevoked,
    },
    institution: institution
      ? {
          institution_id: institution.institution_id,
          name: institution.name,
          type: institution.type,
        }
      : undefined,
    prooflink: {
      action: link.action,
      amount: link.amount,
      currency: link.currency,
      recipient: link.recipient,
      purpose: link.purpose,
      reference_id: link.reference_id,
      issued_at: link.issued_at,
      expires_at: link.expires_at,
      signature_status: 'VALID',
      instruction_status: link.status,
      revocation_status: notRevoked ? 'NOT_REVOKED' : 'REVOKED',
    },
    message:
      result === 'VERIFIED'
        ? 'This instruction is authentic and currently valid.'
        : result === 'EXPIRED'
        ? 'This ProofLink existed but has expired. Treat the instruction as unauthorized.'
        : result === 'REVOKED'
        ? 'This ProofLink was revoked by the issuing institution. Treat the instruction as unauthorized.'
        : 'Verification could not confirm this instruction.',
  }
}
