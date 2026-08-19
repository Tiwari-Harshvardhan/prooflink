import { NavLink, Link } from 'react-router-dom'
import { ShieldCheck, LogOut, User } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth()

  const links = [
    { to: '/verify', label: 'Verify a ProofLink' },
    {
      to: isAuthenticated && user?.role === 'OFFICIAL' ? '/institution' : '/login',
      label: isAuthenticated && user?.role === 'OFFICIAL' ? 'Institution Dashboard' : 'Official Portal'
    },
    { to: '/how-it-works', label: 'How It Works' },
  ]

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
              key={link.label}
              to={link.to}
              className={({ isActive }) =>
                `text-sm font-medium transition-colors ${
                  isActive ? 'text-ink-900 font-semibold' : 'text-ink-500 hover:text-ink-900'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              <Link
                to={user?.role === 'OFFICIAL' ? '/institution' : '/citizen'}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600 bg-brand-50 px-3 py-1.5 rounded-lg hover:bg-brand-100 transition"
              >
                <User className="w-3.5 h-3.5" />
                {user?.name || user?.phone} ({user?.role})
              </Link>
              <button
                onClick={logout}
                title="Logout"
                className="p-2 text-ink-400 hover:text-coral transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link to="/login" className="text-sm font-medium text-ink-600 hover:text-ink-900 mr-2">
              Sign In
            </Link>
          )}
          <NavLink to="/verify" className="hidden sm:inline-flex btn-3d-brand !px-4 !py-2.5">
            Verify Now
          </NavLink>
        </div>
      </div>
    </header>
  )
}
