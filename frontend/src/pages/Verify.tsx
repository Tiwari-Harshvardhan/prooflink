import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Search, ScanLine } from 'lucide-react'
import GradientMesh from '@/components/GradientMesh'
import { useAuth } from '@/context/AuthContext'

export default function Verify() {
  const [prooflink, setProoflink] = useState('')
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const { isAuthenticated, user } = useAuth()
  useEffect(() => { const token = params.get('token'); if (token) setProoflink(token) }, [params])
  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const trimmed = prooflink.trim(); if (!trimmed) return
    if (!isAuthenticated || user?.role !== 'CITIZEN') { navigate('/login'); return }
    navigate(`/verify/result/${encodeURIComponent(trimmed)}`)
  }
  return <div className="relative max-w-2xl mx-auto px-6 py-16 sm:py-20">
    <GradientMesh variant="quiet" />
    <p className="doc-label mb-3">Citizen verification</p>
    <h1 className="font-display text-3xl sm:text-4xl font-bold text-ink-900 mb-3">Verify a ProofLink</h1>
    <p className="text-ink-500 mb-10 max-w-lg leading-relaxed">Paste the trusted ProofLink from your SMS. You must sign in as its verified citizen before its details can be shown.</p>
    <form onSubmit={handleSubmit} className="card p-6 sm:p-8">
      <label htmlFor="prooflink" className="doc-label block mb-2">ProofLink or SMS URL</label>
      <div className="flex flex-col sm:flex-row gap-3"><input id="prooflink" type="text" value={prooflink} onChange={(event) => setProoflink(event.target.value)} placeholder="https://localhost:5173/verify?token=…" className="flex-1 font-mono text-sm border border-ink-100 rounded-xl px-4 py-3 bg-ink-50/60 focus:bg-white focus:border-brand-300 outline-none" autoComplete="off" autoFocus /><button type="submit" disabled={!prooflink.trim()} className="btn-3d-brand"><Search className="w-4 h-4" />Verify</button></div>
      <div className="mt-5 pt-5 border-t border-dashed border-ink-100 flex items-center gap-2 text-ink-500 text-sm"><ScanLine className="w-4 h-4" /><span>The recipient binding is checked by the backend.</span></div>
    </form>
  </div>
}
