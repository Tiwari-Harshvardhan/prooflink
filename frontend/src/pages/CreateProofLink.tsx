import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, QrCode, Copy, Check, ShieldCheck } from 'lucide-react'
import { api } from '@/services/api'
import type { CreateProofLinkRequest, CreateProofLinkResponse } from '@/types'

const initialForm: CreateProofLinkRequest = {
  action: '',
  amount: '',
  currency: 'INR',
  recipient: '',
  purpose: '',
  reference_id: '',
  expires_at: '',
}

export default function CreateProofLink() {
  const [form, setForm] = useState<CreateProofLinkRequest>(initialForm)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<CreateProofLinkResponse | null>(null)
  const [copied, setCopied] = useState(false)

  function update<K extends keyof CreateProofLinkRequest>(key: K, value: CreateProofLinkRequest[K]) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      // The backend signs and creates the instruction — this form never
      // computes or sends a signature.
      const res = await api.createProofLink(form)
      setResult(res)
    } finally {
      setSubmitting(false)
    }
  }

  function copyUrl() {
    if (!result) return
    navigator.clipboard.writeText(result.verification_url)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  if (result) {
    return (
      <div className="max-w-lg mx-auto px-6 py-16 sm:py-20 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-mint text-white mb-6" style={{ boxShadow: '0 6px 0 0 #0F7A38, 0 18px 30px -10px rgba(22,163,74,0.4)' }}>
          <ShieldCheck className="w-8 h-8" />
        </div>
        <h1 className="font-display text-2xl sm:text-3xl font-bold text-ink-900 mb-2">
          ProofLink created and signed
        </h1>
        <p className="text-ink-500 mb-8">
          The instruction has been recorded and cryptographically signed by
          the institution's key on the backend.
        </p>

        <div className="card p-6 sm:p-8 text-left">
          <p className="doc-label mb-2">Proof ID</p>
          <p className="font-mono text-lg text-ink-900 mb-6">{result.proof_id}</p>

          <p className="doc-label mb-2">Verification URL</p>
          <div className="flex items-center gap-2 mb-6">
            <code className="flex-1 text-xs font-mono text-ink-700 bg-ink-50 rounded-lg px-3 py-2.5 truncate">
              {result.verification_url}
            </code>
            <button onClick={copyUrl} type="button" className="chip-3d shrink-0 !py-2.5">
              {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-mint">
              <span className="w-2 h-2 rounded-full bg-mint" />
              <span className="text-sm font-medium">{result.status}</span>
            </div>
            <div className="w-16 h-16 rounded-xl border border-dashed border-ink-200 flex items-center justify-center text-ink-400">
              <QrCode className="w-8 h-8" />
            </div>
          </div>
        </div>

        <div className="mt-8 flex items-center justify-center gap-6">
          <Link to="/institution" className="text-sm font-medium text-ink-700 hover:text-brand-600 transition-colors">
            Back to dashboard
          </Link>
          <button onClick={() => setResult(null)} type="button" className="text-sm font-medium text-ink-700 hover:text-brand-600 transition-colors">
            Create another
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-14 sm:py-16">
      <Link
        to="/institution"
        className="inline-flex items-center gap-1.5 text-sm text-ink-500 hover:text-ink-900 mb-8 transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        Back to dashboard
      </Link>

      <p className="doc-label mb-3">New instruction</p>
      <h1 className="font-display text-3xl sm:text-4xl font-bold text-ink-900 mb-3">
        Create a ProofLink
      </h1>
      <p className="text-ink-500 mb-10 max-w-lg leading-relaxed">
        Describe the instruction exactly as it will be communicated to the
        citizen. The backend signs it with the institution's private key —
        that key never touches this form.
      </p>

      <form onSubmit={handleSubmit} className="card p-6 sm:p-8 space-y-5">
        <TextField label="Action" value={form.action} onChange={(v) => update('action', v)} placeholder="FUND_TRANSFER" required />
        <div className="grid grid-cols-2 gap-4">
          <TextField label="Amount" value={form.amount} onChange={(v) => update('amount', v)} placeholder="80000.00" required />
          <TextField label="Currency" value={form.currency} onChange={(v) => update('currency', v)} placeholder="INR" required />
        </div>
        <TextField label="Recipient" value={form.recipient} onChange={(v) => update('recipient', v)} placeholder="Case Escrow Account #4471" required />
        <TextField label="Purpose" value={form.purpose} onChange={(v) => update('purpose', v)} placeholder="Fraud investigation escrow hold" required />
        <TextField label="Reference ID" value={form.reference_id} onChange={(v) => update('reference_id', v)} placeholder="FIR-2026-778812" required />
        <TextField
          label="Expiry"
          type="datetime-local"
          value={form.expires_at}
          onChange={(v) => update('expires_at', v)}
          required
        />

        <button type="submit" disabled={submitting} className="btn-3d-brand w-full !py-3.5">
          {submitting ? 'Signing and creating…' : 'Create and sign ProofLink'}
        </button>
      </form>
    </div>
  )
}

function TextField({
  label,
  value,
  onChange,
  placeholder,
  required,
  type = 'text',
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  required?: boolean
  type?: string
}) {
  return (
    <div>
      <label className="doc-label block mb-2">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        className="w-full text-sm border border-ink-100 rounded-xl px-4 py-2.5 bg-ink-50/60 focus:bg-white focus:border-brand-300 outline-none transition-colors"
      />
    </div>
  )
}
