// frontend/src/components/MetricCard.jsx
import React from 'react'

export function MetricCard({ title, value, unit, status = 'info', icon: Icon, subtitle }) {
  const statusClass = { good: 'text-good', warn: 'text-warn', crit: 'text-crit', info: 'text-info' }[status] || 'text-info'

  return (
    <div className="card fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span className="card-title">{title}</span>
        {Icon && <Icon size={18} color="var(--text-muted)" />}
      </div>
      <div className={`stat-value ${statusClass}`}>
        {value ?? '—'}
        {unit && <span className="stat-unit">{unit}</span>}
      </div>
      {subtitle && <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{subtitle}</div>}
    </div>
  )
}

export function SeverityBadge({ severity }) {
  const cls = { HEALTHY: 'badge-good', WARNING: 'badge-warn', CRITICAL: 'badge-crit' }[severity] || 'badge-muted'
  const dot = { HEALTHY: 'good', WARNING: 'warn', CRITICAL: 'crit' }[severity] || 'info'
  return (
    <span className={`badge ${cls}`}>
      <span className={`status-dot ${dot}`} />
      {severity}
    </span>
  )
}

export function QoEBadge({ qoeClass }) {
  const cls = { GOOD: 'badge-good', MODERATE: 'badge-warn', POOR: 'badge-crit' }[qoeClass] || 'badge-muted'
  return <span className={`badge ${cls}`}>{qoeClass}</span>
}

export function LoadingState({ message = 'Loading data…' }) {
  return (
    <div className="loading-state">
      <div className="spinner" />
      <span>{message}</span>
    </div>
  )
}

export function ErrorState({ message }) {
  const apiUrl = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : null)

  return (
    <div className="error-state">
      <span style={{ fontSize: '2rem' }}>⚠️</span>
      <strong>Connection Error</strong>
      <span style={{ maxWidth: 400, fontSize: '0.88rem' }}>{message}</span>
      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        {apiUrl ? `Ensure the API backend is running at ${apiUrl}` : 'The API backend is not configured for this deployment.'}
      </span>
    </div>
  )
}
