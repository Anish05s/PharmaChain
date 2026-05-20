import { useState } from 'react'

function EyeIcon({ open }) {
  if (open) {
    return (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5" aria-hidden>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1 1 0 0 1 0-.644C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .644C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
      </svg>
    )
  }
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c1.573 0 3.07-.33 4.415-.923M21.98 15.777A10.47 10.47 0 0 0 22.066 12c-1.292-4.338-5.31-7.5-10.066-7.5-1.573 0-3.07.33-4.415.923M9.75 9.75l4.5 4.5M14.25 9.75l-4.5 4.5" />
    </svg>
  )
}

export default function PasswordInput({ className = '', ...props }) {
  const [visible, setVisible] = useState(false)

  return (
    <div className="relative w-full">
      <input
        {...props}
        type={visible ? 'text' : 'password'}
        className={`w-full px-4 py-3 pr-11 text-sm ${className}`.trim()}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded transition-colors"
        style={{ color: '#64748b' }}
        onMouseEnter={e => e.currentTarget.style.color = '#94a3b8'}
        onMouseLeave={e => e.currentTarget.style.color = '#64748b'}
        aria-label={visible ? 'Hide password' : 'Show password'}
      >
        <EyeIcon open={!visible} />
      </button>
    </div>
  )
}
