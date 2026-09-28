import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { UserPlus } from 'lucide-react'

export default function Register() {
  const [tab, setTab] = useState<'citizen' | 'official'>('citizen')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const { registerCitizen, registerOfficial } = useAuth()
  const navigate = useNavigate()

  // Controlled states for citizen registration to avoid browser autofill
  const [citizenName, setCitizenName] = useState('')
  const [citizenPhone, setCitizenPhone] = useState('')
  const [citizenPassword, setCitizenPassword] = useState('')
  const [citizenAadhaar, setCitizenAadhaar] = useState('')

  // Controlled states for official registration
  const [officialName, setOfficialName] = useState('')
  const [officialPhone, setOfficialPhone] = useState('')
  const [officialPassword, setOfficialPassword] = useState('')
  const [officialInstitutionId, setOfficialInstitutionId] = useState('')
  const [officialId, setOfficialId] = useState('')

  const handleCitizenRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsLoading(true)

    try {
      await registerCitizen(citizenName, citizenPhone, citizenPassword, citizenAadhaar)
      setSuccess('Registration successful! Please verify your OTP.')
      setTimeout(() => navigate('/citizen-verify-otp?phone=' + encodeURIComponent(citizenPhone)), 1500)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleOfficialRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsLoading(true)

    try {
      await registerOfficial(officialName, officialPhone, officialPassword, officialInstitutionId, officialId)
      setSuccess('Registration successful! Please login to continue.')
      setTimeout(() => navigate('/login'), 1500)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 via-ink-900 to-brand-900 flex items-center justify-center px-4 py-8">
      <div className="card max-w-md w-full">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-brand-500 text-white flex items-center justify-center mx-auto mb-4">
            <UserPlus className="w-6 h-6" />
          </div>
          <h1 className="font-display text-2xl font-bold text-ink-900 mb-2">Register</h1>
          <p className="text-ink-500">Create your PROOFLINK account</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-ink-200">
          <button
            type="button"
            onClick={() => setTab('citizen')}
            className={`flex-1 py-3 text-sm font-medium transition ${
              tab === 'citizen'
                ? 'border-b-2 border-brand-500 text-brand-500'
                : 'text-ink-600 hover:text-ink-900'
            }`}
          >
            Citizen
          </button>
          <button
            type="button"
            onClick={() => setTab('official')}
            className={`flex-1 py-3 text-sm font-medium transition ${
              tab === 'official'
                ? 'border-b-2 border-brand-500 text-brand-500'
                : 'text-ink-600 hover:text-ink-900'
            }`}
          >
            Official
          </button>
        </div>

        {/* Citizen Form */}
        {tab === 'citizen' && (
          <form onSubmit={handleCitizenRegister} className="space-y-4" autoComplete="off">
            <div>
              <label className="block text-sm font-medium text-ink-900 mb-1">Name</label>
              <input
                type="text"
                name="citizen_name"
                value={citizenName}
                onChange={(e) => setCitizenName(e.target.value)}
                placeholder="Enter your full name"
                autoComplete="off"
                data-lpignore="true"
                required
                className="w-full px-4 py-2 rounded-lg border border-ink-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ink-900 mb-1">Phone Number</label>
              <input
                type="tel"
                name="citizen_phone"
                value={citizenPhone}
                onChange={(e) => setCitizenPhone(e.target.value)}
                placeholder="Enter phone number"
                autoComplete="off"
                data-lpignore="true"
                required
                className="w-full px-4 py-2 rounded-lg border border-ink-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ink-900 mb-1">Password</label>
              <input
                type="password"
                name="citizen_password"
                value={citizenPassword}
                onChange={(e) => setCitizenPassword(e.target.value)}
                placeholder="Enter password"
                autoComplete="new-password"
                data-lpignore="true"
                required
                className="w-full px-4 py-2 rounded-lg border border-ink-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ink-900 mb-1">Aadhaar Number</label>
              <input
                type="text"
                name="citizen_aadhaar"
                value={citizenAadhaar}
                onChange={(e) => setCitizenAadhaar(e.target.value)}
                placeholder="Enter 12-digit Aadhaar number"
                autoComplete="off"
                data-lpignore="true"
                required
                className="w-full px-4 py-2 rounded-lg border border-ink-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition"
              />
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-coral/10 text-coral text-sm">
                {error}
              </div>
            )}

            {success && (
              <div className="p-3 rounded-lg bg-mint/10 text-mint text-sm">
                {success}
              </div>
            )}

            <button type="submit" disabled={isLoading} className="w-full btn-3d-brand">
              {isLoading ? 'Registering...' : 'Register as Citizen'}
            </button>
          </form>
        )}

        {/* Official Form */}
        {tab === 'official' && (
          <form onSubmit={handleOfficialRegister} className="space-y-4" autoComplete="off">
            <div>
              <label className="block text-sm font-medium text-ink-900 mb-1">Name</label>
              <input
                type="text"
                name="official_name"
                value={officialName}
                onChange={(e) => setOfficialName(e.target.value)}
                placeholder="Enter your full name"
                autoComplete="off"
                data-lpignore="true"
                required
                className="w-full px-4 py-2 rounded-lg border border-ink-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ink-900 mb-1">Phone Number</label>
              <input
                type="tel"
                name="official_phone"
                value={officialPhone}
                onChange={(e) => setOfficialPhone(e.target.value)}
                placeholder="Enter phone number"
                autoComplete="off"
                data-lpignore="true"
                required
                className="w-full px-4 py-2 rounded-lg border border-ink-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ink-900 mb-1">Password</label>
              <input
                type="password"
                name="official_password"
                value={officialPassword}
                onChange={(e) => setOfficialPassword(e.target.value)}
                placeholder="Enter password"
                autoComplete="new-password"
                data-lpignore="true"
                required
                className="w-full px-4 py-2 rounded-lg border border-ink-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ink-900 mb-1">Institution</label>
              <select
                name="official_institution_id"
                value={officialInstitutionId}
                onChange={(e) => setOfficialInstitutionId(e.target.value)}
                required
                className="w-full px-4 py-2 rounded-lg border border-ink-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition"
              >
                <option value="">Select Institution</option>
                <option value="POLICE-MP-001">Madhya Pradesh Police</option>
                <option value="SBI-HQ-001">State Bank of India</option>
                <option value="TRAI-GOV-001">TRAI</option>
                <option value="CBI-HQ-001">CBI</option>
                <option value="HDFC-SEC-001">HDFC Bank</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-ink-900 mb-1">Official ID</label>
              <input
                type="text"
                name="official_id_field"
                value={officialId}
                onChange={(e) => setOfficialId(e.target.value)}
                placeholder="Enter official ID"
                autoComplete="off"
                data-lpignore="true"
                required
                className="w-full px-4 py-2 rounded-lg border border-ink-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition"
              />
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-coral/10 text-coral text-sm">
                {error}
              </div>
            )}

            {success && (
              <div className="p-3 rounded-lg bg-mint/10 text-mint text-sm">
                {success}
              </div>
            )}

            <button type="submit" disabled={isLoading} className="w-full btn-3d-brand">
              {isLoading ? 'Registering...' : 'Register as Official'}
            </button>
          </form>
        )}

        <div className="mt-6 text-center">
          <p className="text-ink-600 text-sm">
            Already have an account?{' '}
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="text-brand-500 font-medium hover:underline"
            >
              Login here
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
