import api from './client'

export async function getManufacturerEmergencyNotifications() {
  const { data } = await api.get('/manufacturer/emergency-notifications')
  return data
}

export async function getSupplierEmergencyNotifications() {
  const { data } = await api.get('/supplier/emergency-notifications')
  return data
}
