import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user')
    return saved ? JSON.parse(saved) : null
  })

  function saveSession(data) {
    localStorage.setItem('token', data.access_token)
    const profile = {
      role: data.role,
      sub_role: data.sub_role,
      full_name: data.full_name,
      entity_id: data.entity_id,
    }
    localStorage.setItem('user', JSON.stringify(profile))
    setUser(profile)
  }

  function logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, saveSession, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}