import { Database, KeyRound, Server, MonitorSmartphone } from 'lucide-react'
import GradientMesh from '@/components/GradientMesh'

const steps = [
  {
    n: '01',
    title: 'Institution issues an instruction',
    body: 'The institution describes the action, amount, recipient, purpose, and expiry through its dashboard.',
  },
  {
    n: '02',
    title: 'Backend signs it with Ed25519',
    body: 'The FastAPI backend computes a SHA-256 content hash and signs it with the institution\u2019s private key. The private key never leaves that layer.',
  },
  {
    n: '03',
    title: 'ProofLink is recorded',
    body: 'The signed instruction is stored in the PROOFLINK registry under a unique Proof ID, alongside the institution\u2019s public key for later verification.',
  },
  {
    n: '04',
    title: 'Citizen checks the Proof ID',
    body: 'Anyone who receives the instruction can independently look up the Proof ID here \u2014 no account or relationship with the institution required.',
  },
  {
    n: '05',
    title: 'Result is returned, not asserted',
    body: 'The backend re-verifies the signature, expiry, and revocation status server-side and returns one of six results. The frontend only renders it.',
  },
]

const layers = [
  {
    icon: MonitorSmartphone,
    title: 'Frontend',
    color: 'bg-brand-100 text-brand-600',
    body: 'React interface for citizens and institutions. Calls the API; never verifies or signs anything itself.',
  },
  {
    icon: Server,
    title: 'Backend',
    color: 'bg-violet/10 text-violet-600',
    body: 'FastAPI service that owns verification logic and issues signed instructions on request.',
  },
  {
    icon: KeyRound,
    title: 'Cryptography',
    color: 'bg-sunset/10 text-sunset-600',
    body: 'Ed25519 signing and SHA-256 hashing, isolated from both the frontend and the general backend logic.',
  },
  {
    icon: Database,
    title: 'Database',
    color: 'bg-mint/10 text-mint-600',
    body: 'PostgreSQL registry of institutions, ProofLinks, and revocations \u2014 public keys only, never private keys.',
  },
]

export default function HowItWorks() {
  return (
    <div className="relative max-w-4xl mx-auto px-6 py-14 sm:py-16">
      <GradientMesh variant="quiet" />
      <p className="doc-label mb-3">Architecture</p>
      <h1 className="font-display text-3xl sm:text-4xl font-bold text-ink-900 mb-4">
        How PROOFLINK works
      </h1>
      <p className="text-ink-500 max-w-xl leading-relaxed mb-14">
        PROOFLINK separates concerns deliberately: the frontend never signs
        or verifies anything on its own, and the database never stores a
        private key. Every trust decision happens once, on the backend.
      </p>

      <div className="mb-16">
        {steps.map((step, i) => (
          <div key={step.n} className="flex gap-6 sm:gap-8">
            <div className="flex flex-col items-center">
              <span className="font-mono text-xs text-white bg-brand-500 rounded-full w-6 h-6 flex items-center justify-center pt-0">
                {i + 1}
              </span>
              {i < steps.length - 1 && <span className="w-px flex-1 bg-ink-100 my-2" />}
            </div>
            <div className="pb-10">
              <h3 className="font-display text-lg font-semibold text-ink-900 mb-1.5">
                {step.title}
              </h3>
              <p className="text-sm text-ink-500 leading-relaxed max-w-lg">{step.body}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="border-t border-ink-100 pt-14">
        <p className="doc-label mb-8">The four layers</p>
        <div className="grid sm:grid-cols-2 gap-4">
          {layers.map(({ icon: Icon, title, body, color }) => (
            <div key={title} className="card p-6">
              <span className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 ${color}`}>
                <Icon className="w-5 h-5" strokeWidth={1.9} />
              </span>
              <h3 className="font-display font-semibold text-ink-900 mb-1.5">{title}</h3>
              <p className="text-sm text-ink-500 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
