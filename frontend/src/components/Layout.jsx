import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import EmergencyNotificationBar from './EmergencyNotificationBar'
import NotificationBell from './NotificationBell'

const ROLE_NAV = {
  manufacturer: [
    { to: '/manufacturer', label: 'Dashboard', icon: '⚡' },
    { to: '/manufacturer/batch/create', label: 'Create Batch', icon: '＋' },
    { to: '/manufacturer/dispatch', label: 'Dispatch', icon: '🚚' },
  ],
  supplier: [
    { to: '/supplier', label: 'Dashboard', icon: '⚡' },
  ],
  consumer: [
    { to: '/hospital', label: 'Dashboard', icon: '⚡' },
  ],
}

const ROLE_GRADIENT = {
  manufacturer: 'linear-gradient(135deg,#0891b2,#3b82f6)',
  supplier:     'linear-gradient(135deg,#7c3aed,#6d28d9)',
  consumer:     'linear-gradient(135deg,#059669,#047857)',
}

function ProfileDropdown({ handleLogout }) {
  const [open, setOpen] = useState(false)
  const dropdownRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        type="button" 
        onClick={() => setOpen(!open)}
        className="w-10 h-10 rounded-full flex items-center justify-center transition-colors"
        style={{ background: '#ffffff', border: '1px solid var(--border)' }}
        onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-base)'}
        onMouseLeave={e => e.currentTarget.style.background = '#ffffff'}
      >
        <svg className="w-5 h-5" style={{ color: 'var(--text-light)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg py-2 z-50 animate-slide-up" style={{ border: '1px solid var(--border)' }}>
          <button 
            type="button"
            className="w-full text-left px-4 py-2 text-sm font-semibold transition-colors"
            style={{ color: 'var(--text-base)' }}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-base)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            My Profile
          </button>
          
          <div className="px-2 mt-1 pt-1" style={{ borderTop: '1px solid var(--border)' }}>
            <button 
              type="button"
              onClick={handleLogout}
              className="w-full text-left px-3 py-2 text-sm font-bold rounded-lg transition-all duration-300"
              style={{ color: '#ef4444', background: 'transparent', border: '1px solid transparent' }}
              onMouseEnter={e => {
                e.currentTarget.style.background = 'rgba(239,68,68,0.06)'
                e.currentTarget.style.border = '1px solid rgba(239,68,68,0.3)'
                e.currentTarget.style.boxShadow = '0 0 12px rgba(239,68,68,0.15)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = 'transparent'
                e.currentTarget.style.border = '1px solid transparent'
                e.currentTarget.style.boxShadow = 'none'
              }}
            >
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function Layout({ title, children, actions }) {
  const { user, logout } = useAuth()
  const navigate  = useNavigate()
  const location  = useLocation()

  function handleLogout() { logout(); navigate('/login') }

  const links    = ROLE_NAV[user?.role] || []
  const gradient = ROLE_GRADIENT[user?.role] || ROLE_GRADIENT.manufacturer
  const initial  = (user?.full_name || user?.email || 'U')[0].toUpperCase()

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--bg-base)', color: 'var(--text-base)' }}>
      {/* ─── Sidebar ─────────────────────────────────────────── */}
      <aside
        className="w-64 flex-shrink-0 flex flex-col"
        style={{ background: '#ffffff', borderRight: '1px solid var(--border)' }}
      >
        {/* Logo */}
        <div className="p-6 pb-4">
          <Link to="/" className="flex items-center gap-3 group">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-lg group-hover:scale-105 transition-transform"
              style={{ background: gradient }}
            >P</div>
            <div>
              <p className="font-bold text-lg leading-none" style={{ color: 'var(--text-base)' }}>PharmaChain</p>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-light)' }}>AI Supply Chain</p>
            </div>
          </Link>
        </div>

        {/* User card */}
        <div className="mx-4 mb-6 p-3 rounded-xl" style={{ background: 'var(--bg-base)', border: '1px solid var(--border)' }}>
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold text-sm mb-2 shadow"
            style={{ background: gradient }}
          >{initial}</div>
          <p className="text-sm font-semibold truncate" style={{ color: 'var(--text-base)' }}>{user?.full_name || user?.email}</p>
          {user?.org_name && <p className="text-xs mt-0.5 truncate font-semibold" style={{ color: 'var(--text-base)' }}>{user.org_name}</p>}
          <p className="text-xs mt-0.5 capitalize" style={{ color: 'var(--text-light)' }}>{user?.sub_role?.replace(/_/g, ' ')}</p>
          {user?.entity_id && <p className="text-[10px] mt-2 truncate uppercase font-semibold" style={{ color: 'var(--text-muted)' }}>ID: {user.entity_id}</p>}
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 space-y-1">
          {links.map(({ to, label, icon }) => {
            const active = location.pathname === to
            return (
              <Link
                key={to}
                to={to}
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200"
                style={active
                  ? { background: 'rgba(8,145,178,0.08)', color: 'var(--cyan)', border: '1px solid rgba(8,145,178,0.18)' }
                  : { color: 'var(--text-muted)' }}
                onMouseEnter={e => {
                  if (!active) {
                    e.currentTarget.style.background = 'var(--bg-base)';
                    e.currentTarget.style.color = 'var(--text-base)';
                  }
                }}
                onMouseLeave={e => {
                  if (!active) {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = 'var(--text-muted)';
                  }
                }}
              >
                <span>{icon}</span>
                {label}
                {active && <span className="ml-auto w-1.5 h-1.5 rounded-full" style={{ background: 'var(--cyan)' }} />}
              </Link>
            )
          })}

          <div className="pt-3 mt-3" style={{ borderTop: '1px solid var(--border)' }}>
            {[
              { to: '/approval-log', icon: '📋', label: 'Audit Log' },
              { to: '/crisis',       icon: '🌍', label: 'Crisis Map' },
            ].map(({ to, icon, label }) => {
              const active = location.pathname === to
              return (
                <Link
                  key={to}
                  to={to}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 mt-1"
                  style={active
                    ? { background: 'rgba(8,145,178,0.08)', color: 'var(--cyan)', border: '1px solid rgba(8,145,178,0.18)' }
                    : { color: 'var(--text-muted)' }}
                  onMouseEnter={e => {
                    if (!active) {
                      e.currentTarget.style.background = 'var(--bg-base)';
                      e.currentTarget.style.color = 'var(--text-base)';
                    }
                  }}
                  onMouseLeave={e => {
                    if (!active) {
                      e.currentTarget.style.background = 'transparent';
                      e.currentTarget.style.color = 'var(--text-muted)';
                    }
                  }}
                >
                  <span>{icon}</span>{label}
                </Link>
              )
            })}
          </div>
        </nav>

        {/* Bottom */}
      </aside>

      {/* ─── Main ────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header
          className="flex items-center justify-between px-8 py-4"
          style={{ borderBottom: '1px solid var(--border)', background: '#ffffff' }}
        >
          <h1 className="font-bold text-lg" style={{ color: 'var(--text-base)' }}>{title}</h1>
          <div className="flex items-center gap-4">
            {actions}
            {actions && <div className="h-6 w-px bg-slate-200"></div>}
            <NotificationBell />
            <ProfileDropdown handleLogout={handleLogout} />
          </div>
        </header>

        <EmergencyNotificationBar />

        <main className="flex-1 overflow-auto p-8">
          <div className="animate-slide-up">{children}</div>
        </main>
      </div>
    </div>
  )
}
