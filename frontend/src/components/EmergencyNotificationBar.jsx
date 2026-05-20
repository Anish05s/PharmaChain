import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import {
  getManufacturerEmergencyNotifications,
  getSupplierEmergencyNotifications,
} from '../api/emergency'

const URGENCY_META = {
  critical: { bg: 'rgba(220,38,38,0.08)',  color: '#dc2626', border: 'rgba(220,38,38,0.2)',  label: '🔴 Critical' },
  high:     { bg: 'rgba(217,119,6,0.08)', color: '#d97706', border: 'rgba(217,119,6,0.2)', label: '🟡 High' },
  normal:   { bg: 'rgba(8,145,178,0.08)',   color: '#0891b2', border: 'rgba(8,145,178,0.2)',  label: 'Normal' },
}

function requesterLabel(type) {
  if (type === 'supplier') return 'Supplier'
  if (type === 'consumer') return 'Hospital / NGO'
  return type
}

export default function EmergencyNotificationBar() {
  const { user } = useAuth()
  const [items,   setItems]   = useState([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    if (!user || (user.role !== 'manufacturer' && user.role !== 'supplier')) {
      setItems([]); setLoading(false); return
    }
    try {
      const data = user.role === 'manufacturer'
        ? await getManufacturerEmergencyNotifications()
        : await getSupplierEmergencyNotifications()
      setItems(data)
    } catch {
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    load()
    const interval = setInterval(load, 45000)
    return () => clearInterval(interval)
  }, [load])

  if (!user || (user.role !== 'manufacturer' && user.role !== 'supplier')) return null
  if (loading || items.length === 0) return null

  return (
    <div
      className="px-8 py-3"
      style={{ background: 'rgba(220,38,38,0.06)', borderBottom: '1px solid rgba(220,38,38,0.15)' }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse inline-block" />
        <p className="text-xs font-bold text-red-600 uppercase tracking-wider">
          {items.length} Emergency Stock Request{items.length > 1 ? 's' : ''}
        </p>
      </div>

      <ul className="space-y-2 max-h-32 overflow-y-auto">
        {items.map((item) => {
          const urgency = (item.urgency || 'normal').toLowerCase()
          const meta    = URGENCY_META[urgency] || URGENCY_META.normal
          return (
            <li
              key={item.id}
              className="flex flex-wrap items-center gap-2 text-xs px-3 py-2 rounded-lg"
              style={{ background: '#ffffff', border: '1px solid var(--border)' }}
            >
              <span
                className="text-xs font-bold px-2 py-0.5 rounded-full flex-shrink-0"
                style={{ background: meta.bg, color: meta.color, border: `1px solid ${meta.border}` }}
              >
                {meta.label}
              </span>
              <span className="text-slate-400 flex-shrink-0 font-bold">{requesterLabel(item.requester_type)}</span>
              <span className="text-slate-800 flex-1 font-semibold">
                <span className="font-bold">{item.requester_name}</span>
                {user.role === 'manufacturer' && item.requester_type === 'consumer' && (
                  <span className="text-slate-400"> → {item.target_name}</span>
                )}
                {' · '}
                <span className="font-bold" style={{ color: 'var(--cyan)' }}>{item.medicine_name}</span>
                {' × '}{item.quantity_requested?.toLocaleString()} units
                {item.reason && <span className="text-slate-400 font-medium font-serif italic"> — "{item.reason}"</span>}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
