import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'

/**
 * NotificationBell — polls /notifications/unread-count every 30s.
 * Clicking opens a dropdown with the 10 latest notifications.
 * Marking read calls PATCH /notifications/{id}/read.
 */
export default function NotificationBell() {
  const { user } = useAuth()
  const [count, setCount] = useState(0)
  const [open, setOpen] = useState(false)
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(false)
  const dropdownRef = useRef(null)

  // Poll unread count every 30 seconds
  useEffect(() => {
    if (!user) return
    let mounted = true

    const fetchCount = async () => {
      try {
        const { data } = await api.get('/notifications/unread-count')
        if (mounted) setCount(data.count)
      } catch {
        // silent — don't disrupt the UI if the endpoint is temporarily unreachable
      }
    }

    fetchCount()
    const interval = setInterval(fetchCount, 30_000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [user])

  // Close on outside click
  useEffect(() => {
    function handler(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  async function handleOpen() {
    setOpen((prev) => !prev)
    if (!open) {
      setLoading(true)
      try {
        const { data } = await api.get('/notifications?limit=10')
        setNotifications(data)
      } catch {
        // silent
      } finally {
        setLoading(false)
      }
    }
  }

  async function markRead(id) {
    try {
      await api.post(`/notifications/${id}/read`)
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      )
      setCount((c) => Math.max(0, c - 1))
    } catch {
      // silent
    }
  }

  async function markAllRead() {
    try {
      await api.post('/notifications/read-all')
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
      setCount(0)
    } catch {
      // silent
    }
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell button */}
      <button
        id="notification-bell-btn"
        onClick={handleOpen}
        className="relative p-2 rounded-lg transition-all"
        style={{ color: 'var(--text-light)' }}
        onMouseEnter={e => e.currentTarget.style.background = 'var(--border)'}
        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
        aria-label="Notifications"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
        </svg>
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse"
            style={{ background: '#ef4444' }}>
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-80 rounded-2xl z-50 overflow-hidden animate-slide-up"
          style={{ background: '#ffffff', border: '1px solid var(--border)', boxShadow: 'var(--shadow-lg)' }}
        >
          <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: '1px solid var(--border)' }}>
            <h3 className="font-bold text-sm" style={{ color: 'var(--text-base)' }}>Notifications</h3>
            {count > 0 && (
              <button onClick={markAllRead} className="text-xs font-bold transition-opacity hover:opacity-70" style={{ color: 'var(--cyan)' }}>
                Mark all read
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <svg className="animate-spin h-5 w-5" style={{ color: 'var(--cyan)' }} viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              </div>
            ) : notifications.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-8 font-semibold">No notifications yet</p>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className="px-4 py-3 cursor-pointer transition-colors"
                  style={{ borderBottom: '1px solid var(--border)', opacity: n.read ? 0.6 : 1 }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-base)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  onClick={() => !n.read && markRead(n.id)}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-base mt-0.5 flex-shrink-0">
                      {n.type === 'stock_alert' ? '⚠️' : n.type === 'flag' ? '🚩' : '🔔'}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-bold text-slate-800 truncate">{n.title}</p>
                      <p className="text-xs text-slate-500 mt-0.5 line-clamp-2 font-medium leading-relaxed">{n.message}</p>
                      <p className="text-[10px] text-slate-400 mt-1 font-semibold">
                        {new Date(n.created_at).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                    {!n.read && (
                      <div className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0" style={{ background: 'var(--cyan)' }} />
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
