import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, ShieldCheck } from 'lucide-react'
import { api } from '@/services/api'
import type { CreateInstructionRequest } from '@/types'

const today = new Date().toISOString().slice(0, 16)
const initialForm: CreateInstructionRequest = {
  citizen_aadhaar_number: '', citizen_phone: '', instruction_id: '', action: 'PAYMENT', amount: 0,
  currency: 'INR', purpose: '', reference_id: '', issued_at: today, due_at: '',
}

export default function CreateProofLink() {
  const [form, setForm] = useState(initialForm)
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const update = (key: keyof CreateInstructionRequest, value: string | number) => setForm((previous) => ({ ...previous, [key]: value } as CreateInstructionRequest))

  async function submit(event: React.FormEvent) {
    event.preventDefault(); setSubmitting(true); setError(null)
    try {
      const result = await api.createInstruction({ ...form, issued_at: new Date(form.issued_at).toISOString(), due_at: new Date(form.due_at).toISOString() })
      setMessage(`${result.message} Notification status: ${result.notification_status}.`)
    } catch (caught: any) {
      setError(caught.response?.data?.detail?.message ?? caught.response?.data?.detail ?? 'Unable to create the instruction.')
    } finally { setSubmitting(false) }
  }

  if (message) return <div className="max-w-lg mx-auto px-6 py-20 text-center">
    <ShieldCheck className="w-16 h-16 text-mint mx-auto mb-6" />
    <h1 className="font-display text-3xl font-bold text-ink-900 mb-3">Instruction created</h1>
    <p className="text-ink-600 leading-relaxed">{message}</p>
    <p className="mt-4 text-sm text-ink-500">For privacy, the ProofLink token is not shown to officials.</p>
    <Link to="/institution" className="btn-3d-brand inline-flex mt-8">Back to dashboard</Link>
  </div>

  return <div className="max-w-2xl mx-auto px-6 py-14">
    <Link to="/institution" className="inline-flex items-center gap-1.5 text-sm text-ink-500 hover:text-ink-900 mb-8"><ArrowLeft className="w-3.5 h-3.5" />Back to dashboard</Link>
    <p className="doc-label mb-3">New official instruction</p>
    <h1 className="font-display text-3xl font-bold text-ink-900 mb-3">Create an instruction</h1>
    <p className="text-ink-500 mb-8">The backend validates the citizen's verified identity, signs the record, and delivers the ProofLink only to that citizen.</p>
    <form onSubmit={submit} className="card p-6 space-y-5">
      <div className="grid sm:grid-cols-2 gap-4"><Field label="Citizen Aadhaar number" value={form.citizen_aadhaar_number} onChange={(v) => update('citizen_aadhaar_number', v)} placeholder="Enter 12-digit Aadhaar" required /><Field label="Citizen mobile number" value={form.citizen_phone} onChange={(v) => update('citizen_phone', v)} placeholder="Enter mobile number" required /></div>
      <div className="grid sm:grid-cols-2 gap-4"><Field label="Instruction ID" value={form.instruction_id} onChange={(v) => update('instruction_id', v)} placeholder="Enter instruction ID" required /><Field label="Reference number" value={form.reference_id} onChange={(v) => update('reference_id', v)} placeholder="Enter reference number" required /></div>
      <Field label="Action / order" value={form.action} onChange={(v) => update('action', v)} required />
      <div className="grid sm:grid-cols-2 gap-4"><Field label="Amount" type="number" value={String(form.amount || '')} onChange={(v) => update('amount', Number(v))} required /><Field label="Currency" value={form.currency} onChange={(v) => update('currency', v)} required /></div>
      <Field label="Purpose" value={form.purpose} onChange={(v) => update('purpose', v)} required />
      <div className="grid sm:grid-cols-2 gap-4"><Field label="Issue date" type="datetime-local" value={form.issued_at} onChange={(v) => update('issued_at', v)} required /><Field label="Due date" type="datetime-local" value={form.due_at} onChange={(v) => update('due_at', v)} required /></div>
      {error && <p className="text-sm text-coral">{error}</p>}
      <button disabled={submitting} className="btn-3d-brand w-full !py-3">{submitting ? 'Creating…' : 'Create instruction'}</button>
    </form>
  </div>
}

function Field({ label, value, onChange, type = 'text', placeholder, required }: { label: string; value: string; onChange: (value: string) => void; type?: string; placeholder?: string; required?: boolean }) {
  return <label className="block"><span className="doc-label block mb-2">{label}</span><input type={type} value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} required={required} className="w-full text-sm border border-ink-100 rounded-xl px-4 py-2.5 bg-ink-50/60 focus:bg-white focus:border-brand-300 outline-none" /></label>
}
