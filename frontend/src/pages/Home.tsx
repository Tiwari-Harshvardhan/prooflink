import { Link } from 'react-router-dom'
import { ArrowRight, PhoneCall, FileSearch, ShieldCheck, Building2 } from 'lucide-react'
import GradientMesh from '@/components/GradientMesh'

export default function Home() {
  return (
    <div>
      {/* Hero */}
      <section className="relative">
        <GradientMesh variant="hero" />
        <div className="max-w-6xl mx-auto px-6 pt-20 pb-16 grid lg:grid-cols-[1.1fr_0.9fr] gap-16 items-center">
          <div>
            <p className="doc-label mb-5">A public verification registry</p>
            <h1 className="font-display text-4xl sm:text-5xl lg:text-[3.4rem] leading-[1.08] text-ink-900 font-bold tracking-tight">
              Don't verify the caller.
              <br />
              <span className="text-brand-500">Verify the instruction.</span>
            </h1>
            <p className="mt-6 text-base sm:text-lg text-ink-500 max-w-lg leading-relaxed">
              When someone claiming to be your bank, police, or a government
              office asks you to act, PROOFLINK checks whether that exact
              instruction was cryptographically authorized — against the
              institution's own registry, not against how convincing the call
              sounded.
            </p>
            <div className="mt-9 flex flex-wrap items-center gap-4">
              <Link to="/verify" className="btn-3d-brand">
                Verify a ProofLink
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link to="/how-it-works" className="btn-3d-white">
                See how it works
              </Link>
            </div>
          </div>

          {/* Signature element: a floating verification slip card */}
          <div className="card p-6 sm:p-7 max-w-sm mx-auto lg:mx-0 lg:justify-self-end">
            <div className="flex items-center justify-between doc-label mb-4">
              <span>Verification Slip</span>
              <span>No. PL-2026-00123</span>
            </div>
            <div className="space-y-3 text-sm">
              <Row k="Institution" v="Maharashtra Police — Cyber Cell" />
              <Row k="Action" v="Fund Transfer" />
              <Row k="Amount" v="₹80,000.00" />
              <Row k="Signature" v="Ed25519 — valid" mono />
            </div>
            <div className="mt-5 pt-4 border-t border-dashed border-ink-100 flex items-center gap-2 text-mint">
              <ShieldCheck className="w-5 h-5" />
              <span className="font-display font-semibold text-sm uppercase tracking-wide">
                Verified
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Scenario */}
      <section className="max-w-6xl mx-auto px-6 py-16 border-t border-ink-100">
        <p className="doc-label mb-3">A typical call</p>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="card p-6">
            <div className="flex items-center gap-2 text-ink-900 mb-3">
              <span className="w-8 h-8 rounded-lg bg-coral/10 text-coral flex items-center justify-center">
                <PhoneCall className="w-4 h-4" />
              </span>
              <span className="text-sm font-medium">Caller</span>
            </div>
            <p className="font-display text-lg text-ink-900 leading-snug">
              "I'm from the Police Department. Transfer ₹80,000 immediately or
              your account will be frozen."
            </p>
          </div>
          <div className="card p-6">
            <div className="flex items-center gap-2 text-ink-900 mb-3">
              <span className="w-8 h-8 rounded-lg bg-brand-100 text-brand-600 flex items-center justify-center">
                <FileSearch className="w-4 h-4" />
              </span>
              <span className="text-sm font-medium">Citizen</span>
            </div>
            <p className="font-display text-lg text-ink-900 leading-snug">
              "Give me the PROOFLINK." — then checks the Proof ID
              independently, on this site.
            </p>
          </div>
        </div>
      </section>

      {/* What gets checked */}
      <section className="max-w-6xl mx-auto px-6 py-16 border-t border-ink-100">
        <p className="doc-label mb-3">Every check, on the record</p>
        <h2 className="font-display text-2xl text-ink-900 font-semibold mb-8">
          What PROOFLINK actually verifies
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          {[
            'Institution identity',
            'Digital signature',
            'Action and amount',
            'Recipient and purpose',
            'Reference ID',
            'Expiry window',
            'Revocation status',
            'Overall authenticity',
          ].map((item) => (
            <div key={item} className="rounded-xl bg-white border border-ink-100 px-4 py-3.5">
              <span className="text-ink-800">{item}</span>
            </div>
          ))}
        </div>
      </section>

      {/* CTA row */}
      <section className="relative max-w-6xl mx-auto px-6 py-16 border-t border-ink-100 grid sm:grid-cols-2 gap-6">
        <GradientMesh variant="quiet" />
        <Link to="/verify" className="card p-7 hover:-translate-y-0.5 transition-transform group">
          <span className="w-11 h-11 rounded-xl bg-mint/10 text-mint flex items-center justify-center mb-4">
            <ShieldCheck className="w-6 h-6" />
          </span>
          <h3 className="font-display text-lg font-semibold text-ink-900 mb-1.5">
            I received an instruction
          </h3>
          <p className="text-sm text-ink-500 mb-4">
            Enter or scan a Proof ID to check whether it was really
            authorized.
          </p>
          <span className="text-sm font-medium text-brand-600 inline-flex items-center gap-1 group-hover:gap-2 transition-all">
            Verify now <ArrowRight className="w-4 h-4" />
          </span>
        </Link>
        <Link to="/institution" className="card p-7 hover:-translate-y-0.5 transition-transform group">
          <span className="w-11 h-11 rounded-xl bg-brand-100 text-brand-600 flex items-center justify-center mb-4">
            <Building2 className="w-6 h-6" />
          </span>
          <h3 className="font-display text-lg font-semibold text-ink-900 mb-1.5">
            I represent an institution
          </h3>
          <p className="text-sm text-ink-500 mb-4">
            Issue and manage signed ProofLinks for outbound instructions.
          </p>
          <span className="text-sm font-medium text-brand-600 inline-flex items-center gap-1 group-hover:gap-2 transition-all">
            Open dashboard <ArrowRight className="w-4 h-4" />
          </span>
        </Link>
      </section>
    </div>
  )
}

function Row({ k, v, mono }: { k: string; v: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-ink-500">{k}</span>
      <span className={`text-right text-ink-900 ${mono ? 'font-mono text-xs' : 'font-medium'}`}>
        {v}
      </span>
    </div>
  )
}
