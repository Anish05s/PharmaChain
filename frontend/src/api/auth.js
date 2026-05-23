import api from './client'

export async function login(email, password, otp = null) {
  const { data } = await api.post('/auth/login', { email, password, otp })
  return data
}

export async function register(payload) {
  const { data } = await api.post('/auth/register', payload)
  return data
}