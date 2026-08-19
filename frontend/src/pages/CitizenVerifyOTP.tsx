import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Shield } from 'lucide-react'

export default function CitizenVerifyOTP() {
  const [otp, setOtp] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { verifyOTP } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const phone = searchParams.get('phone') || ''

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      if (!phone) {
        throw new Error('Phone number is required')
      }
      await verifyOTP(phone, otp)
      navigate('/citizen')
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : err instanceof Error ? err.message : 'OTP verification failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleResendOTP = async () => {
    setIsLoading(true)
    setError('')
    try {
      const { sendOTP } = await import('@/services/api').then(m => ({ sendOTP: m.api.sendOTP }))
      await sendOTP(phone)
      alert('A new OTP has been sent to ' + phone + '. Check http://localhost:5173/dev/sms-inbox')
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : err instanceof Error ? err.message : 'Failed to resend OTP')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 via-ink-900 to-brand-900 flex items-center justify-center px-4">
      <div className="card max-w-md w-full">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-brand-500 text-white flex items-center justify-center mx-auto mb-4">
            <Shield className="w-6 h-6" />
          </div>
          <h1 className="font-display text-2xl font-bold text-ink-900 mb-2">Verify OTP</h1>
          <p className="text-ink-500 text-sm">
            Enter the 6-digit code sent to <br />
            <span className="font-mono text-ink-700">{phone}</span>
          </p>
        </div>

        {/* Demo Helper Banner */}
        <div className="mb-6 p-3 rounded-xl bg-brand-50 border border-brand-200 text-xs text-brand-900 flex items-center justify-between">
          <span>💡 <strong>Demo Mode</strong>: Test OTP is <code className="font-mono font-bold">123456</code></span>
          <button
            type="button"
            onClick={() => setOtp('123456')}
            className="px-2 py-1 bg-brand-500 text-white rounded font-medium hover:bg-brand-600 transition"
          >
            Auto-fill
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-ink-900 mb-1">
              OTP Code
            </label>
            <input
              type="text"
              placeholder="123456"
              maxLength={6}
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
              className="w-full px-4 py-3 text-center text-2xl font-mono tracking-widest rounded-lg border border-ink-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition"
            />
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-coral/10 text-coral text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || otp.length !== 6}
            className="w-full btn-3d-brand"
          >
            {isLoading ? 'Verifying...' : 'Verify OTP'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-ink-600 text-sm mb-2">Didn't receive the code?</p>
          <button
            type="button"
            onClick={handleResendOTP}
            disabled={isLoading}
            className="text-brand-500 font-medium hover:underline text-sm"
          >
            Resend OTP
          </button>
        </div>
      </div>
    </div>
  )
}
