import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { LogIn } from 'lucide-react'

export default function Login() {
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<'CITIZEN' | 'OFFICIAL'>('CITIZEN')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      await login(phone, password)
      // Redirect based on actual role from AuthContext (populated from backend JWT via /auth/me)
      // We read from the context after login() completes — context.user is set by then.
      // Use a small trick: read from localStorage-backed api to avoid stale closure.
      const freshUser = await import('@/services/api').then(m => m.api.getCurrentUser()).catch(() => null)
      const actualRole = freshUser?.role ?? role
      if (actualRole === 'OFFICIAL') {
        navigate('/institution')
      } else {
        navigate('/citizen')
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : err instanceof Error ? err.message : 'Login failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 via-ink-900 to-brand-900 flex items-center justify-center px-4">
      <div className="card max-w-md w-full">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-brand-500 text-white flex items-center justify-center mx-auto mb-4">
            <LogIn className="w-6 h-6" />
          </div>
          <h1 className="font-display text-2xl font-bold text-ink-900 mb-2">Login</h1>
          <p className="text-ink-500">Access your PROOFLINK account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-ink-900 mb-1">
              Account Type
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setRole('CITIZEN')}
                className={`flex-1 px-4 py-2 rounded-lg font-medium transition ${
                  role === 'CITIZEN'
                    ? 'bg-brand-500 text-white'
                    : 'bg-ink-100 text-ink-600 hover:bg-ink-200'
                }`}
              >
                Citizen
              </button>
              <button
                type="button"
                onClick={() => setRole('OFFICIAL')}
                className={`flex-1 px-4 py-2 rounded-lg font-medium transition ${
                  role === 'OFFICIAL'
                    ? 'bg-brand-500 text-white'
                    : 'bg-ink-100 text-ink-600 hover:bg-ink-200'
                }`}
              >
                Official
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-ink-900 mb-1">
              Phone Number
            </label>
            <input
              type="tel"
              placeholder="+91-9876543210"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-ink-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink-900 mb-1">
              Password
            </label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-ink-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition"
            />
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-coral/10 text-coral text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full btn-3d-brand"
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-ink-600 text-sm">
            Don't have an account?{' '}
            <button
              type="button"
              onClick={() => navigate('/register')}
              className="text-brand-500 font-medium hover:underline"
            >
              Register here
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
