import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, ScanLine } from 'lucide-react'
import GradientMesh from '@/components/GradientMesh'

export default function Verify() {
  const [proofId, setProofId] = useState('')
  const navigate = useNavigate()

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = proofId.trim()
    if (!trimmed) return
    navigate(`/verify/result/${encodeURIComponent(trimmed)}`)
  }

  return (
    <div className="relative max-w-2xl mx-auto px-6 py-16 sm:py-20">
      <GradientMesh variant="quiet" />
      <p className="doc-label mb-3">Citizen verification</p>
      <h1 className="font-display text-3xl sm:text-4xl font-bold text-ink-900 mb-3">
        Verify a ProofLink
      </h1>
      <p className="text-ink-500 mb-10 max-w-lg leading-relaxed">
        Enter the Proof ID the caller gave you. We'll check it against the
        authoritative registry — nothing about the call itself is assessed.
      </p>

      <form onSubmit={handleSubmit} className="card p-6 sm:p-8">
        <label htmlFor="proof-id" className="doc-label block mb-2">
          Proof ID
        </label>
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            id="proof-id"
            type="text"
            value={proofId}
            onChange={(e) => setProofId(e.target.value)}
            placeholder="PL-2026-00123"
            className="flex-1 font-mono text-sm border border-ink-100 rounded-xl px-4 py-3 bg-ink-50/60 focus:bg-white focus:border-brand-300 outline-none transition-colors"
            autoComplete="off"
            autoFocus
          />
          <button type="submit" disabled={!proofId.trim()} className="btn-3d-brand">
            <Search className="w-4 h-4" />
            Verify
          </button>
        </div>

        <div className="mt-5 pt-5 border-t border-dashed border-ink-100 flex items-center gap-2 text-ink-500 text-sm">
          <ScanLine className="w-4 h-4" />
          <span>Or scan the QR code shown alongside the instruction.</span>
        </div>
      </form>

      <div className="mt-8 text-sm text-ink-500">
        <p className="mb-3">Try a demo Proof ID:</p>
        <div className="flex flex-wrap gap-2">
          {['PL-2026-00123', 'PL-2026-00098', 'PL-2026-00071', 'PL-2099-XXXXX'].map((id) => (
            <button key={id} type="button" onClick={() => setProofId(id)} className="chip-3d">
              {id}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
