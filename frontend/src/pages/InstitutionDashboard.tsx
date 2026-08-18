import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Building2 } from 'lucide-react'
import { api } from '@/services/api'
import type { Institution, InstitutionStats, ProofLink, ProofLinkStatus } from '@/types'

// Demo institution until the backend provides real session/auth context.
const DEMO_INSTITUTION_ID = 'INST-POLICE-MH-014'

const STATUS_STYLE: Record<ProofLinkStatus, string> = {
  ACTIVE: 'bg-mint/10 text-mint',
  EXPIRED: 'bg-amber/10 text-amber',
  REVOKED: 'bg-coral/10 text-coral',
}

export default function InstitutionDashboard() {
  const [institution, setInstitution] = useState<Institution | null>(null)
  const [stats, setStats] = useState<InstitutionStats | null>(null)
  const [links, setLinks] = useState<ProofLink[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.getInstitution(DEMO_INSTITUTION_ID),
      api.getInstitutionStats(DEMO_INSTITUTION_ID),
      api.getInstitutionProofLinks(DEMO_INSTITUTION_ID),
    ]).then(([inst, s, l]) => {
      setInstitution(inst)
      setStats(s)
      setLinks(l)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return <div className="max-w-6xl mx-auto px-6 py-24 text-center doc-label">Loading dashboard…</div>
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-14 sm:py-16">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6 mb-10">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-brand-500 text-white flex items-center justify-center shrink-0">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <p className="doc-label mb-1">Institution dashboard</p>
            <h1 className="font-display text-2xl sm:text-3xl font-bold text-ink-900">
              {institution?.name ?? 'Unknown Institution'}
            </h1>
            <p className="text-xs font-mono text-ink-500 mt-0.5">{institution?.institution_id}</p>
          </div>
        </div>
        <Link to="/institution/create" className="btn-3d-brand shrink-0">
          <Plus className="w-4 h-4" />
          Create ProofLink
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
        <StatCard label="Total ProofLinks" value={stats?.total ?? 0} />
        <StatCard label="Active" value={stats?.active ?? 0} accent="text-mint" />
        <StatCard label="Expired" value={stats?.expired ?? 0} accent="text-amber" />
        <StatCard label="Revoked" value={stats?.revoked ?? 0} accent="text-coral" />
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ink-100 text-left doc-label">
                <th className="px-5 py-3 font-normal">Proof ID</th>
                <th className="px-5 py-3 font-normal">Action</th>
                <th className="px-5 py-3 font-normal">Amount</th>
                <th className="px-5 py-3 font-normal">Recipient</th>
                <th className="px-5 py-3 font-normal">Status</th>
                <th className="px-5 py-3 font-normal">Created</th>
                <th className="px-5 py-3 font-normal">Expires</th>
              </tr>
            </thead>
            <tbody>
              {links.map((link) => (
                <tr key={link.proof_id} className="border-b border-ink-50 last:border-b-0 hover:bg-brand-50/40">
                  <td className="px-5 py-3.5 font-mono text-xs text-ink-900">{link.proof_id}</td>
                  <td className="px-5 py-3.5 text-ink-800">{humanizeAction(link.action)}</td>
                  <td className="px-5 py-3.5 text-ink-800">
                    {Number(link.amount) > 0 ? `${link.currency} ${Number(link.amount).toLocaleString()}` : '—'}
                  </td>
                  <td className="px-5 py-3.5 text-ink-800 max-w-[180px] truncate">{link.recipient}</td>
                  <td className="px-5 py-3.5">
                    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_STYLE[link.status]}`}>
                      {link.status}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-ink-500 whitespace-nowrap">{formatDate(link.created_at)}</td>
                  <td className="px-5 py-3.5 text-ink-500 whitespace-nowrap">{formatDate(link.expires_at)}</td>
                </tr>
              ))}
              {links.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-5 py-10 text-center text-ink-500">
                    No ProofLinks issued yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, accent }: { label: string; value: number; accent?: string }) {
  return (
    <div className="card p-5">
      <p className="doc-label mb-2">{label}</p>
      <p className={`font-display text-3xl font-bold ${accent ?? 'text-ink-900'}`}>{value}</p>
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
    return new Date(iso).toLocaleDateString(undefined, { dateStyle: 'medium' })
  } catch {
    return iso
  }
}
