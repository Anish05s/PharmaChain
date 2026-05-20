import { useEffect, useState } from 'react'

export default function HandoffForm({
  onSubmit,
  onCancel,
  submitting,
  submitLabel,
  defaultQuantity = 1000,
}) {
  const [form, setForm] = useState({
    quantity_reported: defaultQuantity,
    expiry_reported:   '2028-01-01',
    temp_reported:     24,
    notes:             '',
  })

  useEffect(() => {
    setForm((f) => ({ ...f, quantity_reported: defaultQuantity }))
  }, [defaultQuantity])

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit({
      quantity_reported: Number(form.quantity_reported),
      expiry_reported:   `${form.expiry_reported}T00:00:00`,
      temp_reported:     Number(form.temp_reported),
      notes:             form.notes || undefined,
    })
  }

  const inputStyle = {
    background:   '#ffffff',
    border:       '1px solid var(--border-strong)',
    color:        'var(--text-base)',
    borderRadius: '0.625rem',
    padding:      '0.5rem 0.75rem',
    fontSize:     '0.8125rem',
    width:        '100%',
    outline:      'none',
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-3 mt-3 p-4 rounded-xl"
      style={{ background: 'var(--bg-base)', border: '1px solid var(--border)' }}
    >
      <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Handoff attestation</p>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5 block">
            Qty reported
          </label>
          <input
            type="number" min={1} required style={inputStyle}
            value={form.quantity_reported}
            onChange={(e) => update('quantity_reported', e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5 block">
            Expiry date
          </label>
          <input
            type="date" required style={inputStyle}
            value={form.expiry_reported}
            onChange={(e) => update('expiry_reported', e.target.value)}
          />
        </div>
      </div>

      <div>
        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5 block">
          Storage temp (°C)
        </label>
        <input
          type="number" step="0.1" style={inputStyle}
          value={form.temp_reported}
          onChange={(e) => update('temp_reported', e.target.value)}
        />
      </div>

      <div>
        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5 block">
          Notes
        </label>
        <textarea
          rows={2} style={{ ...inputStyle, resize: 'none' }}
          placeholder="Cold chain maintained, packaging intact…"
          value={form.notes}
          onChange={(e) => update('notes', e.target.value)}
        />
      </div>

      <div className="flex gap-2 pt-1">
        <button
          type="submit"
          disabled={submitting}
          className="px-4 py-2 rounded-lg text-xs font-bold text-white transition-all hover:scale-105 disabled:opacity-50"
          style={{ background: 'linear-gradient(135deg,#059669,#047857)', boxShadow: '0 4px 10px rgba(5,150,105,0.18)' }}
        >
          {submitting ? 'Submitting…' : submitLabel}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="text-xs font-bold px-3 py-2 rounded-lg transition-colors"
            style={{ color: 'var(--text-light)' }}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--border)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}
