import { NavLink } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'

const links = [
  { to: '/verify', label: 'Verify a ProofLink' },
  { to: '/institution', label: 'Institution Dashboard' },
  { to: '/how-it-works', label: 'How It Works' },
]

export default function Navbar() {
  return (
    <header className="sticky top-0 z-30 bg-canvas/90 backdrop-blur-md border-b border-ink-100/70">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <NavLink to="/" className="flex items-center gap-2.5">
          <span className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-4.5 h-4.5 text-white" strokeWidth={2} />
          </span>
          <span className="font-display font-semibold text-lg tracking-tight text-ink-900">
            PROOFLINK
          </span>
        </NavLink>
        <nav className="hidden md:flex items-center gap-8">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `text-sm font-medium transition-colors ${
                  isActive ? 'text-ink-900' : 'text-ink-500 hover:text-ink-900'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <NavLink to="/verify" className="hidden sm:inline-flex btn-3d-brand !px-4 !py-2.5">
          Verify Now
        </NavLink>
      </div>
    </header>
  )
}
