import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import PasswordInput from '../components/PasswordInput'

const DEMO = [
  { role: 'Manufacturer', email: 'manufacturer@pharmachain.com', color: '#0891b2' },
  { role: 'Supplier',     email: 'supplier@pharmachain.com',     color: '#7c3aed' },
  { role: 'Hospital',     email: 'hospital@pharmachain.com',     color: '#059669' },
]

export default function Login() {
  const [email,    setEmail]    = useState('manufacturer@pharmachain.com')
  const [password, setPassword] = useState('PharmaChain2026!')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const { user, saveSession } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!user) return
    if (user.role === 'manufacturer') navigate('/manufacturer', { replace: true })
    else if (user.role === 'supplier') navigate('/supplier', { replace: true })
    else if (user.role === 'consumer') navigate('/hospital', { replace: true })
  }, [user, navigate])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await login(email, password)
      saveSession(data)
      if (data.role === 'manufacturer') navigate('/manufacturer')
      else if (data.role === 'supplier') navigate('/supplier')
      else if (data.role === 'consumer') navigate('/hospital')
      else navigate('/')
    } catch {
      setError('Invalid email or password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--bg-base)' }}>
      {/* Left panel — feature list */}
      <div
        className="hidden lg:flex lg:w-1/2 flex-col justify-center px-16"
        style={{ background: 'linear-gradient(135deg, #e0f2fe 0%, #f0fdf4 100%)', borderRight: '1px solid var(--border)' }}
      >
        <div className="animate-slide-up">
          {/* Logo mark */}
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center text-white font-bold text-3xl shadow-lg mb-8"
            style={{ background: 'linear-gradient(135deg,#0891b2,#3b82f6)' }}
          >P</div>

          <h1 className="text-5xl font-black mb-3 leading-tight" style={{ color: 'var(--text-base)' }}>
            Pharma<span className="gradient-text">Chain</span>
          </h1>
          <p className="text-xl mb-12 leading-relaxed max-w-md" style={{ color: 'var(--text-muted)' }}>
            AI + Blockchain pharmaceutical supply chain integrity for the other 6 billion.
          </p>

          <div className="space-y-3 max-w-md">
            {[
              { icon: '🔐', t: 'Three-Party Attestation', d: 'Fraud requires simultaneous collusion across all three parties — always on-chain.' },
              { icon: '⛓️', t: 'Immutable Blockchain Records', d: 'Every handoff recorded on Ethereum Sepolia. Tamper-proof audit trail.' },
              { icon: '🤖', t: 'Explainable AI Flags', d: 'Risk score 0–100 with human-readable explanation on every cross-match.' },
              { icon: '🌍', t: 'Crisis-Aware Rerouting', d: 'NewsAPI + NetworkX detects floods & conflicts and reroutes supply chains.' },
            ].map(({ icon, t, d }) => (
              <div
                key={t}
                className="flex items-start gap-4 p-4 rounded-xl"
                style={{ background: '#ffffff', border: '1px solid var(--border)', boxShadow: 'var(--shadow-sm)' }}
              >
                <span className="text-2xl flex-shrink-0">{icon}</span>
                <div>
                  <p className="font-semibold text-sm" style={{ color: 'var(--text-base)' }}>{t}</p>
                  <p className="text-xs mt-0.5 leading-relaxed" style={{ color: 'var(--text-light)' }}>{d}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden text-center mb-8">
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-xl mx-auto mb-3"
              style={{ background: 'linear-gradient(135deg,#0891b2,#3b82f6)' }}
            >P</div>
            <h1 className="text-2xl font-bold" style={{ color: 'var(--text-base)' }}>PharmaChain</h1>
          </div>

          <div
            className="p-8 rounded-2xl animate-slide-up"
            style={{ background: '#ffffff', border: '1px solid var(--border)', boxShadow: 'var(--shadow-lg)' }}
          >
            <div className="mb-7">
              <h2 className="text-2xl font-bold" style={{ color: 'var(--text-base)' }}>Welcome back</h2>
              <p className="text-sm mt-1" style={{ color: 'var(--text-light)' }}>Sign in to your portal</p>
            </div>

            {error && (
              <div
                className="mb-5 px-4 py-3 rounded-xl text-sm flex items-center gap-2"
                style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.2)', color: '#ef4444' }}
              >
                <span>⚠️</span> {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 block">Email</label>
                <input
                  id="login-email"
                  type="email"
                  className="w-full px-4 py-3 text-sm"
                  placeholder="you@pharmachain.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 block">Password</label>
                <PasswordInput
                  id="login-password"
                  placeholder="Your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>

              <button
                id="login-submit"
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl font-semibold text-sm text-white transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed mt-1"
                style={{ background: 'linear-gradient(135deg,#0891b2,#3b82f6)', boxShadow: '0 4px 16px rgba(8,145,178,0.2)' }}
              >
                {loading
                  ? <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                      </svg>
                      Signing in…
                    </span>
                  : 'Sign in'}
              </button>
            </form>

            <p className="text-center text-sm mt-6" style={{ color: 'var(--text-light)' }}>
              New here?{' '}
              <Link to="/signup" className="font-semibold transition-colors" style={{ color: 'var(--cyan)' }}>
                Create account
              </Link>
            </p>
          </div>

          {/* Demo accounts */}
          <div
            className="mt-4 p-4 rounded-xl"
            style={{ background: '#ffffff', border: '1px solid var(--border)', boxShadow: 'var(--shadow-sm)' }}
          >
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider text-center mb-3">Quick demo access</p>
            <div className="grid grid-cols-3 gap-2">
              {DEMO.map(({ role, email: e, color }) => (
                <button
                  key={role}
                  type="button"
                  onClick={() => { setEmail(e); setPassword('PharmaChain2026!') }}
                  className="text-xs py-2 px-2 rounded-lg text-center transition-all font-semibold"
                  style={{ color }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-base)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  {role}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}