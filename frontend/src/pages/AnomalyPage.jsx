// frontend/src/pages/AnomalyPage.jsx
import React, { useCallback } from 'react'
import { AlertTriangle } from 'lucide-react'
import { usePoll } from '../hooks/useApi'
import { api } from '../services/api'
import { SeverityBadge, LoadingState, ErrorState } from '../components/MetricCard'

export default function AnomalyPage() {
  const fetcher = useCallback(() => api.anomalies(50), [])
  const { data, loading, error } = usePoll(fetcher, 8000)

  if (loading && !data) return <LoadingState />
  if (error) return <ErrorState message={error} />

  const anomalies = data?.anomalies || []
  const total     = data?.total_anomalies_in_window || 0
  const window_   = data?.window_size || 0

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title"><AlertTriangle size={24} /> Anomaly Detection</h1>
        <p className="page-subtitle">
          Isolation Forest results — {total} anomalies detected in the last {window_} observations
        </p>
      </div>

      {/* ── Stats row ─────────────────────────────── */}
      <div className="grid-3" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-title">Anomalies in Window</div>
          <div className="stat-value text-crit">{total}</div>
        </div>
        <div className="card">
          <div className="card-title">Window Size</div>
          <div className="stat-value text-info">{window_}</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Recent observations</div>
        </div>
        <div className="card">
          <div className="card-title">Anomaly Rate</div>
          <div className="stat-value text-warn">
            {window_ > 0 ? ((total / window_) * 100).toFixed(1) : 0}%
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>of recent window</div>
        </div>
      </div>

      {/* ── Model info ─────────────────────────────── */}
      <div className="card" style={{ marginBottom: 20, background: 'rgba(56,189,248,0.04)' }}>
        <div className="card-title">Model Information</div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: 1.7 }}>
          <strong style={{ color: 'var(--text-primary)' }}>Algorithm:</strong> Isolation Forest (scikit-learn) ·{' '}
          <strong style={{ color: 'var(--text-primary)' }}>Contamination:</strong> 10% ·{' '}
          <strong style={{ color: 'var(--text-primary)' }}>Features:</strong> Latency, Packet Loss, Jitter, Throughput, Bandwidth Utilization, Router CPU, Router Memory, Network Stress
        </p>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: 8 }}>
          ⚠️ The anomaly score is the Isolation Forest raw score. More negative values indicate greater isolation (more anomalous). 
          This score is NOT a probability. Anomaly detection identifies unusual patterns, not confirmed fault root causes.
        </p>
      </div>

      {/* ── Anomaly table ──────────────────────────── */}
      <div className="card">
        <div className="card-title" style={{ marginBottom: 12 }}>
          {anomalies.length > 0 ? `Recent Anomalous Observations (${anomalies.length})` : 'No anomalies in current window'}
        </div>
        {anomalies.length === 0 ? (
          <div className="empty-state">
            <span style={{ fontSize: '2rem' }}>✅</span>
            <span>No anomalies detected in the current observation window.</span>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Scenario</th>
                  <th>Anomaly Score</th>
                  <th>Latency (ms)</th>
                  <th>Packet Loss (%)</th>
                  <th>Bandwidth (%)</th>
                  <th>QoE</th>
                  <th>Health</th>
                </tr>
              </thead>
              <tbody>
                {anomalies.map((rec, i) => (
                  <tr key={i}>
                    <td>{new Date(rec.timestamp).toLocaleTimeString()}</td>
                    <td>
                      <span className="badge badge-warn">
                        {rec.scenario?.toUpperCase().replace(/-/g, ' ')}
                      </span>
                    </td>
                    <td style={{ color: 'var(--status-crit)', fontFamily: 'var(--font-mono)' }}>
                      {rec.anomaly?.anomaly_score?.toFixed(4)}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>
                      {rec.telemetry?.latency_ms?.toFixed(1)}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>
                      {rec.telemetry?.packet_loss_percent?.toFixed(2)}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>
                      {rec.telemetry?.bandwidth_utilization_percent?.toFixed(1)}
                    </td>
                    <td>
                      <span className={`badge ${
                        rec.qoe?.qoe_class === 'GOOD' ? 'badge-good' :
                        rec.qoe?.qoe_class === 'MODERATE' ? 'badge-warn' : 'badge-crit'
                      }`}>
                        {rec.qoe?.qoe_class}
                      </span>
                    </td>
                    <td style={{ color: rec.analysis?.health_score >= 70 ? 'var(--status-good)' : rec.analysis?.health_score >= 40 ? 'var(--status-warn)' : 'var(--status-crit)' }}>
                      {rec.analysis?.health_score?.toFixed(0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
