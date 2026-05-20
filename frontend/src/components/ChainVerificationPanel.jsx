/**
 * ChainVerificationPanel
 * Shared component used by Manufacturer, Supplier, and Hospital dashboards.
 * Renders a RoleVerificationResponse with leg-by-leg breakdown.
 */

const STATUS_CONFIG = {
  VERIFIED: { from: '#059669', to: '#047857', glow: 'rgba(5,150,105,0.08)', icon: '✅', label: 'VERIFIED',  border: 'rgba(5,150,105,0.25)' },
  FLAGGED:  { from: '#dc2626', to: '#b91c1c', glow: 'rgba(220,38,38,0.08)',  icon: '🚩', label: 'FLAGGED',   border: 'rgba(220,38,38,0.25)'  },
  PENDING:  { from: '#d97706', to: '#b45309', glow: 'rgba(217,119,6,0.08)', icon: '⏳', label: 'PENDING',   border: 'rgba(217,119,6,0.25)' },
}

const LEG_ICON = {
  manufacturer_to_supplier: '🏭→🏬',
  supplier_to_hospital:     '🏬→🏥',
}

const FIELD_STATUS = {
  MATCH:         { icon: '✅', color: '#059669' },
  VERIFIED:      { icon: '✅', color: '#059669' },
  LOW_DEVIATION: { icon: '⚠️', color: '#d97706' },
  DEVIATION:     { icon: '🚨', color: '#dc2626' },
  MISMATCH:      { icon: '⚠️', color: '#dc2626' },
  PENDING:       { icon: '⏳', color: '#d97706' },
  'N/A':         { icon: '—',  color: '#64748b' },
}

function FieldBadge({ status, label, detail }) {
  const cfg = FIELD_STATUS[status] || FIELD_STATUS['N/A']
  return (
    <div className="flex items-start gap-1.5">
      <span className="text-sm mt-0.5 flex-shrink-0">{cfg.icon}</span>
      <div>
        <span className="text-xs font-bold" style={{ color: cfg.color }}>{label}</span>
        {detail && <p className="text-xs mt-0.5 leading-relaxed font-semibold" style={{ color: 'var(--text-light)' }}>{detail}</p>}
      </div>
    </div>
  )
}

function LegCard({ leg }) {
  const isFlag = leg.qty_status === 'DEVIATION' || leg.expiry_status === 'MISMATCH'
  const isWarn = leg.qty_status === 'LOW_DEVIATION' || leg.temp_status === 'DEVIATION'

  const borderColor = isFlag ? 'rgba(220,38,38,0.25)' : isWarn ? 'rgba(217,119,6,0.25)' : 'rgba(5,150,105,0.2)'
  const bgColor     = isFlag ? 'rgba(220,38,38,0.06)' : isWarn ? 'rgba(217,119,6,0.06)' : 'rgba(5,150,105,0.05)'

  const qtyDetail =
    leg.qty_status === 'MATCH'
      ? `${leg.dispatched_qty?.toLocaleString()} dispatched = ${leg.received_qty?.toLocaleString()} received`
      : leg.qty_status === 'DEVIATION'
        ? `${leg.dispatched_qty?.toLocaleString()} dispatched ≠ ${leg.received_qty?.toLocaleString()} received (${leg.qty_deviation_pct}% deviation)`
        : 'Awaiting confirmation'

  const expiryDetail =
    leg.expiry_status === 'MATCH'
      ? `${leg.batch_expiry ? new Date(leg.batch_expiry).toLocaleDateString() : '—'}`
      : leg.expiry_status === 'MISMATCH'
        ? `Batch: ${leg.batch_expiry ? new Date(leg.batch_expiry).toLocaleDateString() : '?'} | Received: ${leg.received_expiry ? new Date(leg.received_expiry).toLocaleDateString() : '?'}`
        : 'Awaiting confirmation'

  const tempDetail =
    leg.temp_status === 'MATCH'
      ? `${leg.received_temp}°C (within declared range)`
      : leg.temp_status === 'DEVIATION'
        ? `Declared ${leg.declared_temp}°C, received ${leg.received_temp}°C (+${leg.temp_deviation_c}°C)`
        : leg.temp_status === 'N/A'
          ? 'Not reported'
          : 'Awaiting confirmation'

  return (
    <div className="rounded-xl p-4" style={{ background: bgColor, border: `1px solid ${borderColor}` }}>
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">{LEG_ICON[leg.leg] || '📦'}</span>
          <div>
            <p className="font-bold text-slate-800 text-sm">{leg.from_party} → {leg.to_party}</p>
            <p className="text-xs mt-0.5 font-semibold" style={{ color: 'var(--text-light)' }}>
              {leg.medicine_name} · Batch #{leg.batch_number}
              {leg.shipment_code && ` · ${leg.shipment_code}`}
            </p>
          </div>
        </div>
        {isFlag
          ? <span className="text-xs font-bold px-2.5 py-0.5 rounded-full" style={{ background: 'rgba(220,38,38,0.1)', color: '#dc2626', border: '1px solid rgba(220,38,38,0.2)' }}>🚩 FLAG</span>
          : isWarn
            ? <span className="text-xs font-bold px-2.5 py-0.5 rounded-full" style={{ background: 'rgba(217,119,6,0.1)', color: '#d97706', border: '1px solid rgba(217,119,6,0.2)' }}>⚠ GAP</span>
            : <span className="text-xs font-bold px-2.5 py-0.5 rounded-full" style={{ background: 'rgba(5,150,105,0.1)', color: '#059669', border: '1px solid rgba(5,150,105,0.2)' }}>✓ OK</span>
        }
      </div>

      <div className="grid sm:grid-cols-3 gap-3">
        <FieldBadge status={leg.qty_status}    label="Quantity"     detail={qtyDetail}    />
        <FieldBadge status={leg.expiry_status} label="Expiry Date"  detail={expiryDetail} />
        <FieldBadge status={leg.temp_status}   label="Temperature"  detail={tempDetail}   />
      </div>
    </div>
  )
}

export default function ChainVerificationPanel({ report, loading, error, onClose }) {
  if (loading) {
    return (
      <div className="rounded-2xl p-8 flex items-center justify-center gap-3 bg-white"
        style={{ border: '1px solid var(--border)', boxShadow: 'var(--shadow-sm)' }}>
        <svg className="animate-spin h-5 w-5" style={{ color: 'var(--cyan)' }} viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        <span className="text-sm font-semibold" style={{ color: 'var(--text-light)' }}>Running 3-party AI cross-match…</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-2xl p-5 text-sm font-semibold" style={{ background: 'rgba(220,38,38,0.06)', border: '1px solid rgba(220,38,38,0.2)', color: '#dc2626' }}>
        ⚠️ {error}
      </div>
    )
  }

  if (!report) return null

  const cfg = STATUS_CONFIG[report.overall_status] || STATUS_CONFIG.PENDING

  return (
    <div className="rounded-2xl p-5 space-y-4 bg-white"
      style={{ border: `1px solid ${cfg.border}`, boxShadow: `0 4px 16px ${cfg.glow}` }}>

      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">{cfg.icon}</span>
            <span
              className="text-lg font-black"
              style={{ background: `linear-gradient(135deg,${cfg.from},${cfg.to})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}
            >{cfg.label}</span>
            {report.risk_score > 0 && (
              <span className="text-xs font-bold px-2.5 py-0.5 rounded-full"
                style={{ background: `rgba(${report.risk_score > 70 ? '220,38,38' : '217,119,6'},0.1)`,
                  color: report.risk_score > 70 ? '#dc2626' : '#d97706',
                  border: `1px solid rgba(${report.risk_score > 70 ? '220,38,38' : '217,119,6'},0.2)` }}>
                Risk {report.risk_score.toFixed(0)}/100
              </span>
            )}
          </div>
          {report.summary && (
            <p className="text-sm leading-relaxed font-semibold" style={{ color: 'var(--text-light)' }}>{report.summary}</p>
          )}
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-lg leading-none flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center transition-colors"
            style={{ color: 'var(--text-light)' }}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-base)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >✕</button>
        )}
      </div>

      {/* Batch identity strip */}
      <div className="rounded-xl px-4 py-3 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 border"
        style={{ borderColor: 'var(--border)' }}>
        {[
          { label: 'Medicine',      value: report.medicine_name },
          { label: 'Batch #',       value: report.batch_number,   mono: true },
          { label: 'Total Produced',value: report.batch_qty_total ? `${report.batch_qty_total.toLocaleString()} units` : '—' },
          { label: 'Expiry',        value: report.batch_expiry ? new Date(report.batch_expiry).toLocaleDateString('en-IN') : '—' },
        ].map(({ label, value, mono }) => (
          <div key={label}>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-400">{label}</p>
            <p className={`text-sm font-bold text-slate-800 mt-0.5 ${mono ? 'font-mono' : ''}`}>{value || '—'}</p>
          </div>
        ))}
      </div>

      {/* Supply chain legs */}
      {report.legs?.length > 0 ? (
        <div className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Supply Chain Legs ({report.legs.length})
          </p>
          {report.legs.map((leg, i) => <LegCard key={i} leg={leg} />)}
        </div>
      ) : (
        <p className="text-sm text-center py-4 font-semibold" style={{ color: 'var(--text-light)' }}>
          No shipment legs found for this batch yet.
        </p>
      )}
    </div>
  )
}
