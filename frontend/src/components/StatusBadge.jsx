export default function StatusBadge({ status }) {
  const map = {
    VERIFIED:   { bg: 'rgba(16,185,129,0.15)',  color: '#10b981', border: 'rgba(16,185,129,0.3)',  label: '✓ Verified' },
    FLAGGED:    { bg: 'rgba(239,68,68,0.15)',    color: '#ef4444', border: 'rgba(239,68,68,0.3)',    label: '⚠ Flagged' },
    PENDING:    { bg: 'rgba(245,158,11,0.15)',   color: '#f59e0b', border: 'rgba(245,158,11,0.3)',   label: '◷ Pending' },
    delivered:  { bg: 'rgba(16,185,129,0.15)',   color: '#10b981', border: 'rgba(16,185,129,0.3)',   label: '✓ Delivered' },
    pending:    { bg: 'rgba(245,158,11,0.15)',   color: '#f59e0b', border: 'rgba(245,158,11,0.3)',   label: '◷ Pending' },
    in_transit: { bg: 'rgba(6,182,212,0.15)',    color: '#06b6d4', border: 'rgba(6,182,212,0.3)',    label: '→ In Transit' },
    flagged:    { bg: 'rgba(239,68,68,0.15)',    color: '#ef4444', border: 'rgba(239,68,68,0.3)',    label: '⚠ Flagged' },
    normal:     { bg: 'rgba(148,163,184,0.1)',   color: '#94a3b8', border: 'rgba(148,163,184,0.2)',  label: 'Normal' },
    high:       { bg: 'rgba(245,158,11,0.15)',   color: '#f59e0b', border: 'rgba(245,158,11,0.3)',   label: '🔶 High' },
    critical:   { bg: 'rgba(239,68,68,0.15)',    color: '#ef4444', border: 'rgba(239,68,68,0.3)',    label: '🔴 Critical' },
  }
  const s = map[status] || { bg: 'rgba(148,163,184,0.1)', color: '#94a3b8', border: 'rgba(148,163,184,0.2)', label: status || '—' }
  return (
    <span
      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold"
      style={{ background: s.bg, color: s.color, border: `1px solid ${s.border}` }}
    >
      {s.label}
    </span>
  )
}
