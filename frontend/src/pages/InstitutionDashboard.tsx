import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Building2, LogOut } from 'lucide-react'
import { api } from '@/services/api'
import { useAuth } from '@/context/AuthContext'
import type { Instruction } from '@/types'

export default function InstitutionDashboard() {
  const { user, logout, isAuthenticated } = useAuth(); const navigate = useNavigate()
  const [instructions, setInstructions] = useState<Instruction[]>([]); const [loading, setLoading] = useState(true)
  useEffect(() => {
    if (!isAuthenticated) { navigate('/login'); return }
    api.getOfficialInstructions().then(setInstructions).catch(console.error).finally(() => setLoading(false))
  }, [isAuthenticated, navigate])
  if (!isAuthenticated) return null
  const active = instructions.filter((instruction) => instruction.status === 'ACTIVE').length
  const paid = instructions.filter((instruction) => instruction.payment_status === 'PAID').length
  return <div className="max-w-6xl mx-auto px-6 py-14 sm:py-16">
    <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6 mb-10"><div className="flex items-center gap-4"><div className="w-12 h-12 rounded-xl bg-brand-500 text-white flex items-center justify-center"><Building2 className="w-6 h-6" /></div><div><p className="doc-label mb-1">Official Dashboard</p><h1 className="font-display text-2xl sm:text-3xl font-bold text-ink-900">Institution instructions</h1><p className="text-xs font-mono text-ink-500">{user?.name || user?.phone}</p></div></div><div className="flex gap-3"><Link to="/official/instructions/create" className="btn-3d-brand"><Plus className="w-4 h-4" />Create New Instruction</Link><button onClick={() => { logout(); navigate('/') }} className="btn-3d-brand"><LogOut className="w-4 h-4" /></button></div></div>
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10"><Stat label="Total Instructions" value={instructions.length} /><Stat label="Active" value={active} /><Stat label="Paid" value={paid} /><Stat label="Pending" value={instructions.length - paid} /></div>
    <div className="card overflow-hidden"><div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b border-ink-100 text-left doc-label"><th className="px-5 py-3 font-normal">Instruction ID</th><th className="px-5 py-3 font-normal">Amount</th><th className="px-5 py-3 font-normal">Purpose</th><th className="px-5 py-3 font-normal">Due date</th><th className="px-5 py-3 font-normal">Status</th><th className="px-5 py-3 font-normal">Payment</th></tr></thead><tbody>{loading ? <tr><td colSpan={6} className="px-5 py-10 text-center text-ink-500">Loading dashboard…</td></tr> : instructions.map((instruction) => <tr key={instruction.id} className="border-b border-ink-50"><td className="px-5 py-3.5 font-mono text-xs">{instruction.instruction_id}</td><td className="px-5 py-3.5">{instruction.currency} {instruction.amount.toLocaleString()}</td><td className="px-5 py-3.5">{instruction.purpose}</td><td className="px-5 py-3.5">{new Date(instruction.due_at).toLocaleDateString()}</td><td className="px-5 py-3.5">{instruction.status}</td><td className="px-5 py-3.5">{instruction.payment_status}</td></tr>)}{!loading && !instructions.length && <tr><td colSpan={6} className="px-5 py-10 text-center text-ink-500">No instructions issued yet.</td></tr>}</tbody></table></div></div>
  </div>
}
function Stat({ label, value }: { label: string; value: number }) { return <div className="card p-5"><p className="doc-label mb-2">{label}</p><p className="font-display text-3xl font-bold text-ink-900">{value}</p></div> }
