import api from './client'

export async function getFlaggedShipments() {
  const { data } = await api.get('/admin/flags')
  return data
}

export async function overrideFlag(shipmentId, justification) {
  const { data } = await api.post(`/admin/flags/${shipmentId}/override`, { justification })
  return data
}
