// Central API service layer.
//
// Every network call the UI needs goes through this file. Right now
// USE_MOCKS is true and everything resolves against in-memory fixtures
// in ./mockData.ts. When the FastAPI backend is ready, flip USE_MOCKS
// to false (or set VITE_API_BASE_URL) — no UI component needs to change,
// since they only ever import from this module.

import axios from 'axios'
import type {
  HealthResponse,
  Institution,
  InstitutionStats,
  CreateProofLinkRequest,
  CreateProofLinkResponse,
  ProofLink,
  RevokeProofLinkRequest,
  VerifyResponse,
} from '@/types'
import {
  mockInstitutions,
  mockProofLinks,
  mockStatsFor,
  mockVerify,
} from './mockData'

const USE_MOCKS = true
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Simulates realistic network latency for the mock layer so loading
// states in the UI can be built and tested honestly.
function delay<T>(value: T, ms = 500): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms))
}

export const api = {
  async health(): Promise<HealthResponse> {
    if (USE_MOCKS) return delay({ status: 'ok', version: 'mock-0.1.0' }, 200)
    const { data } = await client.get<HealthResponse>('/health')
    return data
  },

  async getInstitution(institutionId: string): Promise<Institution | null> {
    if (USE_MOCKS) {
      const found = mockInstitutions.find((i) => i.institution_id === institutionId)
      return delay(found ?? null)
    }
    const { data } = await client.get<Institution>(`/institutions/${institutionId}`)
    return data
  },

  async getInstitutionProofLinks(institutionId: string): Promise<ProofLink[]> {
    if (USE_MOCKS) {
      return delay(mockProofLinks.filter((p) => p.institution_id === institutionId))
    }
    const { data } = await client.get<ProofLink[]>(`/institutions/${institutionId}/prooflinks`)
    return data
  },

  async getInstitutionStats(institutionId: string): Promise<InstitutionStats> {
    if (USE_MOCKS) return delay(mockStatsFor(institutionId))
    // The spec's API contract doesn't define a dedicated stats endpoint;
    // derive it client-side from the prooflinks list against the real backend.
    const links = await this.getInstitutionProofLinks(institutionId)
    return {
      total: links.length,
      active: links.filter((p) => p.status === 'ACTIVE').length,
      expired: links.filter((p) => p.status === 'EXPIRED').length,
      revoked: links.filter((p) => p.status === 'REVOKED').length,
    }
  },

  async getProofLink(proofId: string): Promise<ProofLink | null> {
    if (USE_MOCKS) {
      const found = mockProofLinks.find((p) => p.proof_id === proofId)
      return delay(found ?? null)
    }
    const { data } = await client.get<ProofLink>(`/prooflinks/${proofId}`)
    return data
  },

  async createProofLink(payload: CreateProofLinkRequest): Promise<CreateProofLinkResponse> {
    if (USE_MOCKS) {
      const year = new Date().getFullYear()
      const proofId = `PL-${year}-${Math.floor(10000 + Math.random() * 89999)}`
      return delay(
        {
          proof_id: proofId,
          verification_url: `${window.location.origin}/verify/result/${proofId}`,
          status: 'ACTIVE',
          qr_placeholder: true,
        },
        700,
      )
    }
    // The backend signs and creates the instruction. The frontend never signs.
    const { data } = await client.post<CreateProofLinkResponse>('/prooflinks', payload)
    return data
  },

  async revokeProofLink(proofId: string, payload: RevokeProofLinkRequest): Promise<void> {
    if (USE_MOCKS) {
      const link = mockProofLinks.find((p) => p.proof_id === proofId)
      if (link) link.status = 'REVOKED'
      await delay(undefined, 400)
      return
    }
    await client.post(`/prooflinks/${proofId}/revoke`, payload)
  },

  async verify(proofId: string): Promise<VerifyResponse> {
    if (USE_MOCKS) return delay(mockVerify(proofId), 800)
    const { data } = await client.post<VerifyResponse>('/verify', { proof_id: proofId })
    return data
  },
}
