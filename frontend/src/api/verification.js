import api from './client'

export async function verifyBatch(batchId) {
  const { data } = await api.post(`/verification-ai/batches/${batchId}/verify`)
  return data
}

export async function getBatchVerification(batchId) {
  const { data } = await api.get(`/verification-ai/batches/${batchId}`)
  return data
}

export async function getFlags(statusFilter) {
  const params = statusFilter ? { status_filter: statusFilter } : {}
  const { data } = await api.get('/verification-ai/flags', { params })
  return data
}

// ── Role-specific chain views ─────────────────────────────────────────────────

/** Manufacturer: full chain (both legs) for a batch */
export async function getManufacturerChain(batchId) {
  const { data } = await api.get(`/verification-ai/manufacturer/batch/${batchId}`)
  return data
}

/** Supplier: incoming + outgoing legs for their incoming shipment */
export async function getSupplierChain(incomingShipmentId) {
  const { data } = await api.get(`/verification-ai/supplier/shipment/${incomingShipmentId}`)
  return data
}

/** Hospital: single-leg + batch identity check for their incoming shipment */
export async function getHospitalChain(incomingShipmentId) {
  const { data } = await api.get(`/verification-ai/hospital/shipment/${incomingShipmentId}`)
  return data
}
