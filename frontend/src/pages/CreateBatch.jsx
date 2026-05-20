import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { createBatch } from '../api/manufacturer'

const initialForm = {
  name: '',
  batch_number: '',
  quantity: '',
  manufacturing_date: '',
  expiry_date: '',
  storage_temp_declared: 25,
}

export default function CreateBatch() {
  const navigate = useNavigate()
  const [form, setForm] = useState(initialForm)
  const [step, setStep] = useState('form') // form | confirm
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function handleReview(e) {
    e.preventDefault()
    setError('')
    if (!form.name.trim() || !form.batch_number.trim() || !form.quantity) {
      setError('Fill in medicine name, batch number, and quantity.')
      return
    }
    if (!form.manufacturing_date || !form.expiry_date) {
      setError('Manufacturing and expiry dates are required.')
      return
    }
    if (form.expiry_date <= form.manufacturing_date) {
      setError('Expiry date must be after manufacturing date.')
      return
    }
    setStep('confirm')
  }

  async function handleConfirm() {
    setError('')
    setSubmitting(true)
    try {
      const payload = {
        name: form.name.trim(),
        batch_number: form.batch_number.trim(),
        quantity: Number(form.quantity),
        storage_temp_declared: Number(form.storage_temp_declared),
        manufacturing_date: `${form.manufacturing_date}T00:00:00`,
        expiry_date: `${form.expiry_date}T00:00:00`,
      }
      const data = await createBatch(payload)
      setSuccess(data)
      setTimeout(() => navigate('/manufacturer'), 2000)
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Failed to create batch')
      setStep('form')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Layout title="Create Batch">
      <Link to="/manufacturer" className="text-sm font-bold transition-opacity hover:opacity-85" style={{ color: 'var(--cyan)' }}>
        ← Back to Dashboard
      </Link>

      <div className="mt-6 max-w-xl animate-slide-up">
        <h1 className="text-2xl font-black mb-2" style={{ color: 'var(--text-base)' }}>New Batch</h1>
        <p className="text-xs font-semibold mb-6" style={{ color: 'var(--text-light)' }}>
          Enter details, review them, then confirm. Creates batch + approval log.
        </p>

        {error && (
          <p className="mb-4 text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm font-semibold">
            ⚠️ {error}
          </p>
        )}

        {success && (
          <div className="mb-4 text-green-700 bg-green-50 border border-green-200 rounded-xl px-4 py-3 text-sm font-semibold">
            <p className="font-bold">Batch created successfully.</p>
            <p className="mt-1">Approval log ID: {success.approval_log_id}</p>
            <p className="mt-1">Redirecting to dashboard…</p>
          </div>
        )}

        {step === 'form' && (
          <form
            onSubmit={handleReview}
            className="rounded-xl p-6 space-y-4"
            style={{ background: '#ffffff', border: '1px solid var(--border)', boxShadow: 'var(--shadow-md)' }}
          >
            <Field label="Medicine name">
              <input
                required
                className="w-full px-4 py-3 text-sm"
                value={form.name}
                onChange={(e) => update('name', e.target.value)}
                placeholder="Paracetamol 500mg"
              />
            </Field>

            <Field label="Batch number">
              <input
                required
                className="w-full px-4 py-3 text-sm"
                value={form.batch_number}
                onChange={(e) => update('batch_number', e.target.value)}
                placeholder="AZMFDPM203L"
              />
            </Field>

            <Field label="Quantity (units)">
              <input
                required
                type="number"
                min={1}
                className="w-full px-4 py-3 text-sm"
                value={form.quantity}
                onChange={(e) => update('quantity', e.target.value)}
                placeholder="15000"
              />
            </Field>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Manufacturing date">
                <input
                  required
                  type="date"
                  className="w-full px-4 py-3 text-sm"
                  value={form.manufacturing_date}
                  onChange={(e) => update('manufacturing_date', e.target.value)}
                />
              </Field>
              <Field label="Expiry date">
                <input
                  required
                  type="date"
                  className="w-full px-4 py-3 text-sm"
                  value={form.expiry_date}
                  onChange={(e) => update('expiry_date', e.target.value)}
                />
              </Field>
            </div>

            <Field label="Storage temp declared (°C)">
              <input
                type="number"
                step="0.1"
                className="w-full px-4 py-3 text-sm"
                value={form.storage_temp_declared}
                onChange={(e) => update('storage_temp_declared', e.target.value)}
              />
            </Field>

            <button
              type="submit"
              className="w-full py-3 rounded-xl font-bold text-sm text-white transition-all duration-200 hover:scale-[1.01]"
              style={{ background: 'linear-gradient(135deg,#0891b2,#3b82f6)', boxShadow: '0 4px 12px rgba(8,145,178,0.2)' }}
            >
              Review details →
            </button>
          </form>
        )}

        {step === 'confirm' && (
          <div className="rounded-xl p-6 space-y-4" style={{ background: '#ffffff', border: '1px solid var(--border)', boxShadow: 'var(--shadow-md)' }}>
            <h2 className="font-bold text-base" style={{ color: 'var(--text-base)' }}>Confirm before creating</h2>
            <dl className="text-sm space-y-2">
              <Row label="Medicine" value={form.name} />
              <Row label="Batch number" value={form.batch_number} />
              <Row label="Quantity" value={`${form.quantity} units`} />
              <Row label="Manufactured" value={form.manufacturing_date} />
              <Row label="Expires" value={form.expiry_date} />
              <Row label="Storage temp" value={`${form.storage_temp_declared} °C`} />
            </dl>
            <p className="text-xs font-semibold bg-amber-50 border border-amber-200 rounded-xl px-3 py-2" style={{ color: 'var(--amber)' }}>
              Check every field. This is logged as a compliance approval (batch_creation).
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setStep('form')}
                className="flex-1 py-2.5 rounded-xl font-bold text-sm transition-all border"
                style={{ color: 'var(--text-muted)', borderColor: 'var(--border)', background: '#ffffff' }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-base)'}
                onMouseLeave={e => e.currentTarget.style.background = '#ffffff'}
              >
                Edit
              </button>
              <button
                type="button"
                disabled={submitting}
                onClick={handleConfirm}
                className="flex-1 py-2.5 rounded-xl font-bold text-sm text-white transition-all hover:scale-[1.01] disabled:opacity-50"
                style={{ background: 'linear-gradient(135deg,#0891b2,#3b82f6)', boxShadow: '0 4px 12px rgba(8,145,178,0.2)' }}
              >
                {submitting ? 'Creating…' : 'Confirm & create batch'}
              </button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5 block">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between gap-4 border-b pb-2" style={{ borderColor: 'var(--border)' }}>
      <dt style={{ color: 'var(--text-light)' }} className="font-semibold">{label}</dt>
      <dd className="font-bold text-right" style={{ color: 'var(--text-base)' }}>{value}</dd>
    </div>
  )
}
