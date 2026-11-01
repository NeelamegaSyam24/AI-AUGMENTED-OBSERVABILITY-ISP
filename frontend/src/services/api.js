// frontend/src/services/api.js
// API client for communicating with the FastAPI backend.

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '')

async function request(path, options = {}) {
  if (!API_BASE) {
    throw new Error('API is not configured for this deployment. Set VITE_API_URL to the deployed API URL.')
  }

  const url = `${API_BASE}${path}`
  try {
    const resp = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }))
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }
    return await resp.json()
  } catch (err) {
    if (err.name === 'TypeError') {
      throw new Error(`Cannot connect to API at ${API_BASE}. Is the backend running?`)
    }
    throw err
  }
}

export const api = {
  health:         () => request('/health'),
  networkSummary: () => request('/network-summary'),
  networkHealth:  () => request('/network-health'),
  anomalies:      (limit = 20) => request(`/anomalies?limit=${limit}`),
  qoe:            () => request('/qoe'),
  predictions:    (limit = 20) => request(`/predictions?limit=${limit}`),
  events:         (limit = 20) => request(`/events?limit=${limit}`),
  scenarios:      () => request('/scenarios'),
  modelInfo:      () => request('/model-info'),

  // Scenario activation
  setScenario: (name) => request(`/scenario/${name}`, { method: 'POST' }),

  // Custom prediction
  predictAnomaly: (telemetry) => request('/predict/anomaly', {
    method: 'POST',
    body: JSON.stringify(telemetry),
  }),
  predictQoE: (telemetry) => request('/predict/qoe', {
    method: 'POST',
    body: JSON.stringify(telemetry),
  }),
}
