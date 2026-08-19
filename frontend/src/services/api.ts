// Central API service layer.
//
// Every network call the UI needs goes through this file. Right now
// USE_MOCKS is false and everything connects to the real FastAPI backend.

import axios, { AxiosInstance } from 'axios'
import type {
  HealthResponse,
  Institution,
  InstitutionStats,
  CreateProofLinkRequest,
  CreateProofLinkResponse,
  CreateInstructionRequest,
  Instruction,
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

const USE_MOCKS = false
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

// Token storage
const TOKEN_KEY = 'prooflink_access_token'
const USER_KEY = 'prooflink_user'

export interface AuthUser {
  user_id: string
  name: string
  phone: string
  role: 'CITIZEN' | 'OFFICIAL' | 'ADMIN'
  email?: string
}

// Create axios client with dynamic headers
function createClient(): AxiosInstance {
  return axios.create({
    baseURL: API_BASE_URL,
    headers: { 'Content-Type': 'application/json' },
  })
}

let client = createClient()

// Update client with auth token
function updateClientToken() {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    client.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete client.defaults.headers.common['Authorization']
  }
}

// Simulates realistic network latency for the mock layer
function delay<T>(value: T, ms = 500): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms))
}

function normalizeVerifyResponse(data: any): VerifyResponse {
  const checks = data.checks ?? {}
  const normalizedChecks = {
    prooflink_exists: Boolean(checks.prooflink_exists ?? checks.exists ?? false),
    institution_recognized: Boolean(checks.institution_recognized ?? false),
    signature_valid: Boolean(checks.signature_valid ?? false),
    instruction_matches: Boolean(checks.instruction_matches ?? true),
    amount_matches: Boolean(checks.amount_matches ?? checks.amount_match ?? false),
    recipient_matches: Boolean(checks.recipient_matches ?? checks.recipient_match ?? false),
    not_expired: Boolean(checks.not_expired ?? false),
    not_revoked: Boolean(checks.not_revoked ?? false),
  }

  const institution = data.institution ?? {}
  const normalizedInstitution = institution.institution_id
    ? institution
    : {
        ...institution,
        institution_id: institution.id ?? institution.institution_id,
      }

  const prooflink = data.prooflink ?? data.instruction ?? {}
  const normalizedProofLink = prooflink.amount != null && typeof prooflink.amount !== 'string'
    ? { ...prooflink, amount: String(prooflink.amount) }
    : prooflink

  return {
    result: data.result ?? data.status ?? 'VERIFIED',
    proof_id: data.proof_id ?? data.proofId ?? '',
    checks: normalizedChecks,
    institution: normalizedInstitution,
    prooflink: normalizedProofLink,
    message: data.message ?? 'Verification completed.',
  }
}

// Token management
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string, user: AuthUser) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
  updateClientToken()
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  updateClientToken()
}

export function getStoredUser(): AuthUser | null {
  const userJson = localStorage.getItem(USER_KEY)
  return userJson ? JSON.parse(userJson) : null
}

export const api = {
  // Auth endpoints
  async registerCitizen(name: string, phone: string, password: string, aadhaar: string) {
    if (USE_MOCKS) {
      return delay({
        user_id: 'USER-' + Math.random().toString(36).substr(2, 9),
        name,
        phone,
        kyc_status: 'VERIFIED',
        message: 'Citizen registered successfully.',
      }, 500)
    }
    const { data } = await client.post('/auth/citizen/register', {
      name,
      phone,
      password,
      aadhaar_number: aadhaar,
    })
    return data
  },

  async registerOfficial(name: string, phone: string, password: string, institutionId: string, officialId: string) {
    if (USE_MOCKS) {
      return delay({
        user_id: 'USER-' + Math.random().toString(36).substr(2, 9),
        name,
        phone,
        institution_id: institutionId,
        message: 'Official registered successfully.',
      }, 500)
    }
    const { data } = await client.post('/auth/official/register', {
      name,
      phone,
      password,
      institution_id: institutionId,
      official_id: officialId,
    })
    return data
  },

  async login(phone: string, password: string) {
    if (USE_MOCKS) {
      const token = 'mock-token-' + Math.random().toString(36)
      const user: AuthUser = {
        user_id: 'USER-1',
        name: 'Demo User',
        phone,
        role: 'CITIZEN',
      }
      setToken(token, user)
      return { access_token: token, token_type: 'bearer', user_id: 'USER-1', role: 'CITIZEN' }
    }
    const { data } = await client.post('/auth/login', { phone, password })
    if (data.access_token) {
      const user: AuthUser = {
        user_id: data.user_id,
        name: '',
        phone,
        role: data.role,
      }
      setToken(data.access_token, user)
    }
    return data
  },

  async sendOTP(phone: string) {
    if (USE_MOCKS) return delay({ status: 'sent', message: 'OTP sent', phone }, 300)
    const { data } = await client.post('/auth/citizen/send-otp', { phone })
    return data
  },

  async verifyOTP(phone: string, otp: string) {
    if (USE_MOCKS) {
      const token = 'mock-token-' + Math.random().toString(36)
      const user: AuthUser = {
        user_id: 'USER-' + Math.random().toString(36).substr(2, 9),
        name: 'Demo Citizen',
        phone,
        role: 'CITIZEN',
      }
      setToken(token, user)
      return { status: 'verified', message: 'OTP verified', access_token: token, token_type: 'bearer' }
    }
    const { data } = await client.post('/auth/citizen/verify-otp', { phone, otp })
    if (data.access_token) {
      const user: AuthUser = {
        user_id: '',
        name: '',
        phone,
        role: 'CITIZEN',
      }
      setToken(data.access_token, user)
    }
    return data
  },

  async getCurrentUser(): Promise<AuthUser> {
    updateClientToken()
    if (USE_MOCKS) {
      return delay(getStoredUser() || {
        user_id: 'USER-1',
        name: 'Demo User',
        phone: '+91-9876543210',
        role: 'CITIZEN',
      }, 200)
    }
    const { data } = await client.get('/auth/me')
    return data
  },

  // Dashboard endpoints
  async getCitizenProofLinks(): Promise<ProofLink[]> {
    updateClientToken()
    if (USE_MOCKS) {
      return delay(mockProofLinks, 500)
    }
    const { data } = await client.get('/dashboard/citizen/prooflinks')
    return data
  },

  async getOfficialProofLinks(): Promise<ProofLink[]> {
    updateClientToken()
    if (USE_MOCKS) {
      return delay(mockProofLinks, 500)
    }
    const { data } = await client.get('/dashboard/official/prooflinks')
    return data
  },

  async getOfficialInstructions() {
    updateClientToken()
    if (USE_MOCKS) return delay([], 500)
    const { data } = await client.get<Instruction[]>('/dashboard/official/instructions')
    return data
  },

  // Original endpoints
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
    const { data } = await client.post<any>('/prooflinks', { ...payload, institution_id: payload.institution_id ?? 'POLICE-MP-001' })
    return {
      proof_id: data.proof_id,
      verification_url: data.verification_url ?? `${window.location.origin}/verify/result/${data.proof_id}`,
      status: data.status,
      qr_placeholder: data.qr_placeholder ?? true,
    }
  },

  async createInstruction(payload: CreateInstructionRequest) {
    updateClientToken()
    const { data } = await client.post('/official/instructions', payload)
    return data as { instruction_id: string; status: string; notification_status: string; message: string }
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

  async verify(prooflink: string): Promise<VerifyResponse> {
    updateClientToken()
    if (USE_MOCKS) return delay(mockVerify(prooflink), 800)
    const { data } = await client.post<any>('/verify', { prooflink })
    return normalizeVerifyResponse(data)
  },

  async createPaymentOrder(prooflink: string) {
    updateClientToken()
    const { data } = await client.post('/payments/create-order', { prooflink })
    return data as { payment_id: string; amount: number; currency: string; status: string; provider: string }
  },

  async confirmPayment(paymentId: string) {
    updateClientToken()
    const { data } = await client.post('/payments/verify', { payment_id: paymentId })
    return data as { payment_id: string; amount: number; currency: string; status: string; provider: string; paid_at?: string }
  },

  async getDevSmsInbox(): Promise<{ messages: Array<{ id: number; phone_number: string; message: string; timestamp: string; status: string }> }> {
    const { data } = await client.get('/dev/sms-inbox')
    return data
  },
}
