// frontend/src/pages/ScenarioPage.jsx
import React, { useCallback, useState } from 'react'
import { Sliders, CheckCircle } from 'lucide-react'
import { usePoll } from '../hooks/useApi'
import { api } from '../services/api'
import { LoadingState, ErrorState } from '../components/MetricCard'

const SCENARIO_META = {
  'normal':         { label: 'Normal Operation', desc: 'ISP network under normal load. Healthy metrics across all indicators.', color: 'var(--status-good)', btnClass: 'btn btn-outline', activeClass: 'btn btn-active' },
  'high-latency':   { label: 'High Latency',     desc: 'Elevated latency (≈180ms) with increased jitter and reduced throughput.', color: 'var(--status-warn)', btnClass: 'btn btn-warn', activeClass: 'btn btn-warn btn-active' },
  'packet-loss':    { label: 'Packet Loss',       desc: 'Significant packet loss (≈7.5%) degrading service reliability.', color: 'var(--status-crit)', btnClass: 'btn btn-danger', activeClass: 'btn btn-danger btn-active' },
  'congestion':     { label: 'Bandwidth Congestion', desc: 'Bandwidth utilization near saturation (≈95%), throughput reduced.', color: 'var(--status-warn)', btnClass: 'btn btn-warn', activeClass: 'btn btn-warn btn-active' },
  'router-overload':{ label: 'Router Overload',   desc: 'Core router under heavy CPU (≈92%) and memory (≈87%) load.', color: 'var(--status-crit)', btnClass: 'btn btn-danger', activeClass: 'btn btn-danger btn-active' },
  'recovery':       { label: 'Network Recovery',  desc: 'Metrics gradually returning to normal after a degradation event.', color: 'var(--accent-cyan)', btnClass: 'btn btn-primary', activeClass: 'btn btn-primary' },
}

export default function ScenarioPage() {
  const [activating, setActivating] = useState(null)
  const [lastResult, setLastResult] = useState(null)
  const [error_, setError_] = useState(null)

  const fetcher = useCallback(() => api.scenarios(), [])
  const { data, loading, error } = usePoll(fetcher, 5000)

  const activate = async (name) => {
    setActivating(name)
    setError_(null)
    try {
      const result = await api.setScenario(name)
      setLastResult({ scenario: name, ...result })
    } catch (err) {
      setError_(`Failed to activate scenario: ${err.message}`)
    } finally {
      setActivating(null)
    }
  }

  if (loading && !data) return <LoadingState />
  if (error) return <ErrorState message={error} />

  const current = data?.current || 'normal'

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title"><Sliders size={24} /> Scenario Control</h1>
        <p className="page-subtitle">
          Activate ISP network simulation scenarios to demonstrate different network conditions.
          Scenario changes are reflected immediately in Prometheus metrics, Grafana dashboards,
          ML predictions, and the events log.
        </p>
      </div>

      {/* ── Current scenario indicator ─────────────── */}
      <div className="card" style={{ marginBottom: 20, background: 'rgba(56,189,248,0.05)', borderColor: 'var(--border-active)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <CheckCircle size={20} color="var(--accent-cyan)" />
          <div>
            <div style={{ fontWeight: 600 }}>Active Scenario</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
              {SCENARIO_META[current]?.label || current.toUpperCase().replace(/-/g, ' ')}
            </div>
          </div>
          <span className="badge badge-info" style={{ marginLeft: 'auto' }}>
            {current.toUpperCase().replace(/-/g, ' ')}
          </span>
        </div>
      </div>

      {error_ && (
        <div className="card" style={{ marginBottom: 20, borderColor: 'rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.08)' }}>
          <span style={{ color: 'var(--status-crit)' }}>{error_}</span>
        </div>
      )}

      {lastResult && (
        <div className="card" style={{ marginBottom: 20, borderColor: 'rgba(34,197,94,0.4)', background: 'rgba(34,197,94,0.06)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--status-good)' }}>
            <CheckCircle size={16} />
            <span>Scenario <strong>{lastResult.display_name || lastResult.scenario}</strong> activated — {lastResult.description}</span>
          </div>
        </div>
      )}

      {/* ── Scenario cards ─────────────────────────── */}
      <div className="grid-2" style={{ marginBottom: 20 }}>
        {Object.entries(SCENARIO_META).map(([name, meta]) => {
          const isActive  = current === name
          const isLoading = activating === name

          return (
            <div
              key={name}
              className="card"
              style={{
                borderColor: isActive ? meta.color : 'var(--border)',
                background: isActive ? `rgba(56,189,248,0.04)` : 'var(--bg-card)',
                transition: 'all 0.3s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <div>
                  <div style={{ fontWeight: 600, color: isActive ? meta.color : 'var(--text-primary)', marginBottom: 4 }}>
                    {meta.label}
                  </div>
                  {isActive && <span className="badge badge-info">ACTIVE</span>}
                </div>
                <div style={{ width: 12, height: 12, borderRadius: '50%', background: meta.color, flexShrink: 0, marginTop: 4 }} />
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: 1.6, marginBottom: 14 }}>
                {meta.desc}
              </p>
              <button
                id={`btn-scenario-${name}`}
                className={isActive ? meta.activeClass : meta.btnClass}
                onClick={() => activate(name)}
                disabled={isActive || isLoading}
                style={{ width: '100%', opacity: (isActive || isLoading) ? 0.7 : 1, cursor: isActive ? 'default' : 'pointer' }}
              >
                {isLoading ? '⏳ Activating…' : isActive ? '✓ Active' : `Activate ${meta.label}`}
              </button>
            </div>
          )
        })}
      </div>

      {/* ── How it works ─────────────────────────────── */}
      <div className="card">
        <div className="card-title">How Scenario Control Works</div>
        <ol style={{ paddingLeft: 20, color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: 2 }}>
          <li>Clicking <em>Activate</em> sends a <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>POST /scenario/&lt;name&gt;</code> request to the FastAPI backend.</li>
          <li>The API proxies the request to the Network Simulator service.</li>
          <li>The simulator's internal state changes to the selected scenario.</li>
          <li>Every subsequent telemetry tick generates metrics matching the new scenario.</li>
          <li>Prometheus scrapes the updated metrics within its configured interval (10s).</li>
          <li>The AI service re-runs anomaly detection and QoE classification on the new telemetry.</li>
          <li>Grafana dashboards refresh automatically (default: 10s).</li>
          <li>This dashboard polls the API every 8 seconds to display updated values.</li>
        </ol>
      </div>
    </div>
  )
}
