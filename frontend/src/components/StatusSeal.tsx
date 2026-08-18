import type { VerificationResult } from '@/types'
import { Check, X, AlertTriangle, HelpCircle, Clock, Ban } from 'lucide-react'

const CONFIG: Record<
  VerificationResult,
  { label: string; bg: string; edge: string; glow: string; Icon: typeof Check }
> = {
  VERIFIED: {
    label: 'Verified',
    bg: '#16A34A',
    edge: '#0F7A38',
    glow: 'rgba(22,163,74,0.35)',
    Icon: Check,
  },
  NOT_FOUND: {
    label: 'Not Found',
    bg: '#5D6B85',
    edge: '#404C63',
    glow: 'rgba(93,107,133,0.3)',
    Icon: HelpCircle,
  },
  MISMATCH: {
    label: 'Mismatch',
    bg: '#E29B0E',
    edge: '#A97407',
    glow: 'rgba(226,155,14,0.35)',
    Icon: AlertTriangle,
  },
  INVALID_SIGNATURE: {
    label: 'Invalid Signature',
    bg: '#EF4759',
    edge: '#B82636',
    glow: 'rgba(239,71,89,0.35)',
    Icon: X,
  },
  EXPIRED: {
    label: 'Expired',
    bg: '#E29B0E',
    edge: '#A97407',
    glow: 'rgba(226,155,14,0.35)',
    Icon: Clock,
  },
  REVOKED: {
    label: 'Revoked',
    bg: '#EF4759',
    edge: '#B82636',
    glow: 'rgba(239,71,89,0.35)',
    Icon: Ban,
  },
}

// A raised, coin-like medallion using the same stacked-shadow technique
// as the 3D buttons elsewhere in the UI, so the "biggest" moment on the
// result page still speaks the same visual language as the rest of it.
export default function StatusSeal({ result }: { result: VerificationResult }) {
  const { label, bg, edge, glow, Icon } = CONFIG[result]

  return (
    <div className="inline-flex flex-col items-center">
      <div
        className="w-32 h-32 sm:w-36 sm:h-36 rounded-full flex items-center justify-center"
        style={{
          background: bg,
          boxShadow: `0 8px 0 0 ${edge}, 0 24px 40px -14px ${glow}`,
        }}
      >
        <div className="flex flex-col items-center gap-2 text-white">
          <Icon className="w-9 h-9 sm:w-10 sm:h-10" strokeWidth={2.25} />
          <span className="font-display font-semibold uppercase tracking-[0.06em] text-xs sm:text-sm text-center px-2 leading-tight">
            {label}
          </span>
        </div>
      </div>
    </div>
  )
}
