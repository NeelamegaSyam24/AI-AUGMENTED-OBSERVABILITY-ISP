// frontend/src/pages/EventsPage.jsx
import React, { useCallback } from 'react'
import { List } from 'lucide-react'
import { usePoll } from '../hooks/useApi'
import { api } from '../services/api'
import { LoadingState, ErrorState } from '../components/MetricCard'

const SEVERITY_STYLE = {
  CRITICAL: { badge: 'badge-crit', dot: 'crit' },
  WARNING:  { badge: 'badge-warn', dot: 'warn' },
  INFO:     { badge: 'badge-info', dot: 'info' },
  HEALTHY:  { badge: 'badge-good', dot: 'good' },
}

export default function EventsPage() {
  const fetcher = useCallback(() => api.events(50), [])
  const { data, loading, error } = usePoll(fetcher, 8000)

  if (loading && !data) return <LoadingState />
  if (error) return <ErrorState message={error} />

  const events = data?.events || []
  const source  = data?.source || 'unknown'

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title"><List size={24} /> Network Events</h1>
        <p className="page-subtitle">
        Recent network events derived from the last 100 AI prediction records — Source: <strong>{source}</strong>
        </p>
      </div>

      {/* ── Legend ─────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        {Object.entries(SEVERITY_STYLE).map(([sev, { badge }]) => (
          <span key={sev} className={`badge ${badge}`}>{sev}</span>
        ))}
      </div>

      {/* ── Event list ─────────────────────────────── */}
      <div className="card">
        <div className="card-title" style={{ marginBottom: 12 }}>
          Recent Network Events ({events.length})
        </div>
        {events.length === 0 ? (
          <div className="empty-state">
            <span style={{ fontSize: '2rem' }}>📋</span>
            <span>No events available yet. The system may still be warming up.</span>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {events.map((ev, i) => {
              const style = SEVERITY_STYLE[ev.severity] || SEVERITY_STYLE['INFO']
              const ts = ev.timestamp || ev['@timestamp']
              const eventType = ev.event_type || ev.scenario?.toUpperCase().replace(/-/g, '_') || 'UNKNOWN'
              const component = ev.component || (ev.metrics ? 'core-router' : 'system')
              const desc = ev.description || ev.explanation || ''

              return (
                <div key={i} className="card" style={{ padding: '14px 16px', background: 'var(--bg-secondary)' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                    <span className={`status-dot ${style.dot}`} style={{ marginTop: 4, flexShrink: 0 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
                        <span className={`badge ${style.badge}`}>{ev.severity || 'INFO'}</span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.88rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                          {eventType}
                        </span>
                        <span className="badge badge-muted">{component}</span>
                        <span style={{ marginLeft: 'auto', fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          {ts ? new Date(ts).toLocaleString() : '—'}
                        </span>
                      </div>
                      {desc && (
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                          {desc}
                        </p>
                      )}
                      {ev.metrics && (
                        <div style={{ display: 'flex', gap: 12, marginTop: 6, flexWrap: 'wrap' }}>
                          {ev.metrics.latency_ms != null && (
                            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                              Latency: <span style={{ color: 'var(--text-secondary)' }}>{ev.metrics.latency_ms?.toFixed(1)}ms</span>
                            </span>
                          )}
                          {ev.metrics.packet_loss_percent != null && (
                            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                              Packet Loss: <span style={{ color: 'var(--text-secondary)' }}>{ev.metrics.packet_loss_percent?.toFixed(2)}%</span>
                            </span>
                          )}
                          {ev.metrics.bandwidth_utilization_percent != null && (
                            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                              BW Util: <span style={{ color: 'var(--text-secondary)' }}>{ev.metrics.bandwidth_utilization_percent?.toFixed(1)}%</span>
                            </span>
                          )}
                          {ev.metrics.throughput_mbps != null && (
                            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                              Throughput: <span style={{ color: 'var(--text-secondary)' }}>{ev.metrics.throughput_mbps?.toFixed(1)} Mbps</span>
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
