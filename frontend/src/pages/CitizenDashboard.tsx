import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/services/api'
import { LogOut, CheckCircle2 } from 'lucide-react'
import type { ProofLink } from '@/types'

export default function CitizenDashboard() {
  const { user, logout, isAuthenticated } = useAuth()
  const [prooflinks, setProoflinks] = useState<ProofLink[]>([])
  const [loading, setLoading] = useState(true)
  const [prooflink, setProoflink] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }

    const loadProoflinks = async () => {
      try {
        const links = await api.getCitizenProofLinks()
        setProoflinks(links)
      } catch (error) {
        console.error('Failed to load prooflinks:', error)
      } finally {
        setLoading(false)
      }
    }

    loadProoflinks()
  }, [isAuthenticated, navigate])

  if (!isAuthenticated) return null

  return (
    <div className="max-w-6xl mx-auto px-6 py-14 sm:py-16">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6 mb-10">
        <div>
          <p className="doc-label mb-1">Citizen Dashboard</p>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-ink-900">
            Welcome, {user?.name || 'Citizen'}
          </h1>
          <p className="text-xs font-mono text-ink-500 mt-0.5">{user?.phone}</p>
        </div>
        <button
          onClick={() => {
            logout()
            navigate('/')
          }}
          className="btn-3d-brand shrink-0 flex items-center gap-2"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>

      <div className="card">
        <form onSubmit={(event) => {
          event.preventDefault()
          const raw = prooflink.trim()
          if (!raw) return
          // If the user pasted a full URL (e.g. https://…/verify?token=PL-xxx),
          // extract the token from the `token` query parameter.
          let token = raw
          try {
            const url = new URL(raw)
            const paramToken = url.searchParams.get('token')
            if (paramToken) token = paramToken
          } catch {
            // raw is not a valid URL — treat it as a bare token
          }
          navigate(`/verify?token=${encodeURIComponent(token)}`)
        }} className="p-6 border-b border-ink-100">
          <label className="doc-label block mb-2">Verify a ProofLink</label>
          <div className="flex gap-3"><input value={prooflink} onChange={(event) => setProoflink(event.target.value)} placeholder="Paste the ProofLink or token from your SMS" className="flex-1 border border-ink-100 rounded-xl px-4 py-2.5 text-sm" /><button className="btn-3d-brand" type="submit">Verify</button></div>
        </form>
        <h2 className="text-lg font-bold text-ink-900 mb-6">Your ProofLinks</h2>

        {loading ? (
          <div className="text-center py-12 text-ink-500">Loading your prooflinks...</div>
        ) : prooflinks.length === 0 ? (
          <div className="text-center py-12 text-ink-500">
            No prooflinks yet. They will appear here when you receive them.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-100 text-left doc-label">
                  <th className="px-5 py-3 font-normal">Proof ID</th>
                  <th className="px-5 py-3 font-normal">Amount</th>
                  <th className="px-5 py-3 font-normal">Purpose</th>
                  <th className="px-5 py-3 font-normal">Status</th>
                  <th className="px-5 py-3 font-normal">Expires</th>
                  <th className="px-5 py-3 font-normal">Action</th>
                </tr>
              </thead>
              <tbody>
                {prooflinks.map((link) => (
                  <tr key={link.proof_id} className="border-b border-ink-100 hover:bg-ink-50">
                    <td className="px-5 py-3 font-mono text-xs font-semibold text-brand-500">
                      {link.proof_id}
                    </td>
                    <td className="px-5 py-3">
                      {link.amount} {link.currency}
                    </td>
                    <td className="px-5 py-3 text-ink-600">{link.purpose}</td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                          link.status === 'ACTIVE'
                            ? 'bg-mint/10 text-mint'
                            : link.status === 'EXPIRED'
                              ? 'bg-amber/10 text-amber'
                              : 'bg-coral/10 text-coral'
                        }`}
                      >
                        <CheckCircle2 className="w-3 h-3" />
                        {link.status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-ink-500 text-xs">
                      {new Date(link.expires_at).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-3">
                      <button
                        onClick={() => navigate(`/verify?token=${encodeURIComponent(link.proof_id)}`)}
                        className="text-brand-500 hover:text-brand-700 font-medium text-sm"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
