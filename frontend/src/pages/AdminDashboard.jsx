import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { getFlaggedShipments, overrideFlag } from '../api/admin'

export default function AdminDashboard() {
  const { user, logout } = useAuth()
  const [flags, setFlags] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedFlag, setSelectedFlag] = useState(null)
  const [justification, setJustification] = useState('')
  const [overriding, setOverriding] = useState(false)
  const [error, setError] = useState('')

  const isDev = user?.sub_role === 'admin_dev'

  async function loadFlags() {
    try {
      const data = await getFlaggedShipments()
      setFlags(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFlags()
  }, [])

  async function handleOverride(e) {
    e.preventDefault()
    if (!justification) return
    setOverriding(true)
    setError('')
    try {
      await overrideFlag(selectedFlag.shipment_id, justification)
      setSelectedFlag(null)
      setJustification('')
      loadFlags()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to override flag')
    } finally {
      setOverriding(false)
    }
  }

  return (
    <div className="min-h-screen text-slate-100 p-8" style={{ background: '#090e17' }}>
      <header className="flex justify-between items-center mb-10 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">Admin<span className="text-cyan-400">CommandCenter</span></h1>
          <p className="text-slate-400 text-sm mt-1">
            Logged in as <span className="font-semibold text-white">{user?.full_name}</span> ({user?.sub_role})
          </p>
        </div>
        <button onClick={logout} className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm font-semibold transition-colors">
          Sign Out
        </button>
      </header>

      <div className="max-w-6xl mx-auto space-y-8">
        <section>
          <h2 className="text-xl font-bold mb-4">Pending AI Flags</h2>
          {loading ? (
            <p className="text-slate-500">Loading flags...</p>
          ) : flags.length === 0 ? (
            <div className="p-12 text-center border border-slate-800 rounded-2xl bg-slate-900/50">
              <p className="text-slate-400">No active AI flags to review.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {flags.map(f => (
                <div key={f.shipment_id} className="p-5 border border-slate-800 rounded-xl bg-slate-900 flex justify-between items-center">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <span className="px-2.5 py-1 text-xs font-bold bg-red-500/20 text-red-400 rounded-md">
                        RISK {f.risk_score}
                      </span>
                      <h3 className="font-semibold">{f.shipment_code} ({f.medicine_name})</h3>
                    </div>
                    <p className="text-sm text-slate-400 max-w-2xl line-clamp-1">{f.explanation}</p>
                  </div>
                  <button 
                    onClick={() => setSelectedFlag(f)}
                    className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-sm rounded-lg transition-colors"
                  >
                    Review
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      {/* Review Modal */}
      {selectedFlag && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-2xl p-8 rounded-2xl border border-slate-800" style={{ background: '#111827' }}>
            <h3 className="text-2xl font-bold mb-4">Review AI Flag</h3>
            
            <div className="p-4 rounded-xl bg-red-950/30 border border-red-900 mb-6">
              <p className="text-sm text-red-200 mb-2 font-mono uppercase tracking-widest text-xs">AI Analysis</p>
              <p className="text-slate-200 leading-relaxed">{selectedFlag.explanation}</p>
            </div>

            {isDev ? (
              <div className="p-4 rounded-xl bg-amber-900/20 border border-amber-900">
                <p className="text-amber-200 font-semibold mb-1">Override Locked</p>
                <p className="text-sm text-amber-300/70">Your role ({user.sub_role}) does not have permission to override compliance flags. You may only view raw data for debugging purposes.</p>
                <div className="flex gap-3 mt-4">
                  <button onClick={() => setSelectedFlag(null)} className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 font-semibold text-sm w-full transition-colors">Close</button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleOverride}>
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Compliance Justification</label>
                    <textarea 
                      required
                      className="w-full px-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-sm min-h-[100px] focus:border-cyan-500 outline-none transition-colors text-white"
                      placeholder="Explain why this shipment is being overridden..."
                      value={justification}
                      onChange={e => setJustification(e.target.value)}
                    />
                  </div>
                  {error && <p className="text-red-400 text-xs">{error}</p>}
                  <div className="flex gap-3 mt-6">
                    <button type="button" onClick={() => setSelectedFlag(null)} className="flex-1 py-2.5 rounded-xl font-semibold text-sm border border-slate-700 hover:bg-slate-800 transition-colors">Cancel</button>
                    <button type="submit" disabled={overriding} className="flex-1 py-2.5 rounded-xl font-semibold text-sm text-white bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 transition-colors">
                      {overriding ? 'Processing...' : 'Override & Approve'}
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
