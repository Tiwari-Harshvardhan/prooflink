import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Loader2, CheckCircle2 } from 'lucide-react'
import { api } from '@/services/api'
import type { VerifyResponse } from '@/types'
import StatusSeal from '@/components/StatusSeal'
import CheckItem from '@/components/CheckItem'

const MESSAGE_BY_RESULT: Record<string, string> = {
  VERIFIED: 'This instruction is authentic and currently valid.',
  NOT_FOUND: 'No ProofLink exists with this ID. Treat the instruction as unauthorized.',
  MISMATCH: 'Details of the instruction do not match the registry record.',
  INVALID_SIGNATURE: 'The digital signature could not be verified.',
  EXPIRED: 'This ProofLink has expired. Treat the instruction as unauthorized.',
  REVOKED: 'This ProofLink was revoked by the issuing institution.',
}

export default function VerifyResult() {
  const rawProofId = useParams<{ proofId: string }>().proofId ?? ''
  // proofId from the URL path may be URL-encoded (e.g. %23 for #). Decode it.
  const proofId = decodeURIComponent(rawProofId)
  const [data, setData] = useState<VerifyResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [paymentMessage, setPaymentMessage] = useState<string | null>(null)
  const [paying, setPaying] = useState(false)

  useEffect(() => {
    if (!proofId) return
    setLoading(true)
    api.verify(proofId).then((res) => {
      setData(res)
      setLoading(false)
    }).catch(() => { setData(null); setLoading(false) })
  }, [proofId])

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-24 flex flex-col items-center text-center">
        <Loader2 className="w-8 h-8 text-brand-400 animate-spin mb-4" />
        <p className="doc-label">Checking the registry…</p>
      </div>
    )
  }

  if (!data) return <div className="max-w-2xl mx-auto px-6 py-24 text-center text-coral">This ProofLink could not be verified for your account.</div>

  const link = data.prooflink

  return (
    <div className="max-w-2xl mx-auto px-6 py-14 sm:py-16">
      <Link
        to="/verify"
        className="inline-flex items-center gap-1.5 text-sm text-ink-500 hover:text-ink-900 mb-8 transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        Verify another ProofLink
      </Link>

      <div className="flex flex-col items-center text-center mb-10">
        <StatusSeal result={data.result} />
        <p className="doc-label mt-6">{data.proof_id}</p>
        <p className="mt-2 text-ink-800 max-w-md leading-relaxed">
          {data.message || MESSAGE_BY_RESULT[data.result]}
        </p>
      </div>

      {link && data.institution && (
        <div className="card p-6 sm:p-8 mb-6">
          <p className="doc-label mb-5">Instruction details</p>
          <dl className="grid sm:grid-cols-2 gap-x-8 gap-y-4 text-sm">
            <Field label="Instruction ID" value={link.reference_id} mono />
            <Field label="Institution" value={data.institution.name} />
            <Field label="Institution ID" value={data.institution.institution_id} mono />
            <Field label="Action" value={humanizeAction(link.action)} />
            <Field
              label="Amount"
              value={
                Number(link.amount) > 0
                  ? `${link.currency} ${Number(link.amount).toLocaleString()}`
                  : '—'
              }
            />
            <Field label="Recipient" value={link.recipient} />
            <Field label="Purpose" value={link.purpose} />
            <Field label="Reference ID" value={link.reference_id} mono />
            <Field label="Issued At" value={formatDate(link.issued_at)} />
            <Field label="Expires At" value={formatDate(link.expires_at)} />
            <Field label="Signature Status" value={link.signature_status} />
            <Field label="Instruction Status" value={link.instruction_status} />
            <Field label="Revocation Status" value={link.revocation_status} />
          </dl>
        </div>
      )}

      <div className="card p-6 sm:p-8">
        <p className="doc-label mb-2">Verification checks</p>
        <ul className="divide-y divide-ink-50">
          <CheckItem label="ProofLink exists in the registry" passed={data.checks.prooflink_exists} />
          <CheckItem label="Institution recognized" passed={data.checks.institution_recognized} />
          <CheckItem label="Signature valid" passed={data.checks.signature_valid} />
          <CheckItem label="Instruction matches" passed={data.checks.instruction_matches} />
          <CheckItem label="Amount matches" passed={data.checks.amount_matches} />
          <CheckItem label="Recipient matches" passed={data.checks.recipient_matches} />
          <CheckItem label="Not expired" passed={data.checks.not_expired} />
          <CheckItem label="Not revoked" passed={data.checks.not_revoked} />
        </ul>
      </div>
      {data.result === 'VERIFIED' && link && (
        <div className="card p-6 sm:p-8 mt-6">
          <p className="doc-label mb-2">Authorized payment</p>
          <p className="text-2xl font-display font-bold text-ink-900">{link.currency} {Number(link.amount).toLocaleString()}</p>

          {link.payment_status === 'PAID' || link.instruction_status === 'PAID' ? (
            <div className="mt-4 p-4 rounded-xl bg-mint/10 border border-mint/30 text-mint">
              <div className="flex items-center gap-2 font-display font-semibold text-base">
                <CheckCircle2 className="w-5 h-5" />
                Payment Completed
              </div>
              <p className="text-xs text-ink-600 mt-1">
                This transaction has been processed and verified on the registry.
                {link.payment_id && <span className="block font-mono text-[11px] mt-1 text-ink-500">Transaction ID: {link.payment_id}</span>}
              </p>
            </div>
          ) : (
            <>
              <p className="text-sm text-ink-500 mt-2">The amount is retrieved from the verified backend instruction and cannot be edited.</p>
              {paymentMessage ? (
                <div className="mt-4 p-4 rounded-xl bg-mint/10 border border-mint/30 text-mint font-medium text-sm">
                  {paymentMessage}
                </div>
              ) : (
                <button
                  disabled={paying}
                  onClick={async () => {
                    setPaying(true)
                    try {
                      const order = await api.createPaymentOrder(data.proof_id)
                      const result = await api.confirmPayment(order.payment_id)
                      setPaymentMessage(`Mock payment successful — ${result.status}.`)
                      // Refresh verification status so state updates immediately
                      api.verify(proofId).then(setData)
                    } catch (err: any) {
                      const detail = err?.response?.data?.detail
                      setPaymentMessage(typeof detail === 'string' ? detail : 'Payment failed')
                    } finally {
                      setPaying(false)
                    }
                  }}
                  className="btn-3d-brand mt-5"
                >
                  {paying ? 'Processing…' : 'Proceed to secure test payment'}
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

function Field({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-xs text-ink-500 mb-0.5">{label}</dt>
      <dd className={`text-ink-900 ${mono ? 'font-mono text-xs' : 'font-medium'}`}>{value}</dd>
    </div>
  )
}

function humanizeAction(action: string): string {
  return action
    .toLowerCase()
    .split('_')
    .map((w) => w[0]?.toUpperCase() + w.slice(1))
    .join(' ')
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    })
  } catch {
    return iso
  }
}
