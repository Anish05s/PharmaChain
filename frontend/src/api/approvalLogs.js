import api from './client'

export async function getApprovalLogs(params = {}) {
  const { data } = await api.get('/approval-logs', { params })
  return data
}
