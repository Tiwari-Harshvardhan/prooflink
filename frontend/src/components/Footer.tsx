import { ShieldCheck } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="border-t border-ink-100 mt-24">
      <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <span className="w-7 h-7 rounded-lg bg-brand-500 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-4 h-4 text-white" strokeWidth={2} />
          </span>
          <div>
            <p className="font-display text-sm font-semibold text-ink-900">PROOFLINK</p>
            <p className="doc-label mt-0.5">Verify the instruction, not the caller</p>
          </div>
        </div>
        <p className="text-xs text-ink-500 max-w-sm leading-relaxed">
          PROOFLINK checks cryptographic authorization records against the
          issuing institution's registry. It does not determine whether a
          phone call, SMS, or email is legitimate on its own.
        </p>
      </div>
    </footer>
  )
}
