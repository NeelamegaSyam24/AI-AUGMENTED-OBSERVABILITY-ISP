// frontend/src/pages/Dashboard.jsx
import React, { useCallback } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, AreaChart, Area, Legend
} from 'recharts'
import { Activity, Wifi, Cpu, AlertTriangle } from 'lucide-react'
import { usePoll } from '../hooks/useApi'
import { api } from '../services/api'
import { MetricCard, SeverityBadge, QoEBadge, LoadingState, ErrorState } from '../components/MetricCard'
import { useRef } from 'react'

const CHART_COLOR_MAP = {
  latency:   '#38bdf8',
  packet:    '#ef4444',
  bandwidth: '#f59e0b',
  throughput:'#22c55e',
  cpu:       '#8b5cf6',
  memory:    '#ec4899',
}

function getLatencyStatus(v) {
  if (v > 140) return 'crit'
  if (v > 80)  return 'warn'
  return 'good'
}
function getPacketLossStatus(v) {
  if (v > 5)  return 'crit'
  if (v > 2)  return 'warn'
  return 'good'
}
function getBwStatus(v) {
  if (v > 92) return 'crit'
  if (v > 80) return 'warn'
  return 'good'
}
function getTpStatus(v) {
  if (v < 40)  return 'crit'
  if (v < 70)  return 'warn'
  return 'good'
}

export default function Dashboard() {
  const historyRef = useRef([])

  const fetcher = useCallback(() => api.networkSummary(), [])
  const { data, loading, error } = usePoll(fetcher, 8000)

  // Build history for charts
  if (data?.telemetry) {
    const t = data.telemetry
    const entry = {
      time:      new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      latency:   +t.latency_ms?.toFixed(1),
      packet:    +t.packet_loss_percent?.toFixed(2),
      bandwidth: +t.bandwidth_utilization_percent?.toFixed(1),
      throughput:+t.throughput_mbps?.toFixed(1),
      cpu:       +t.router_cpu_percent?.toFixed(1),
      memory:    +t.router_memory_percent?.toFixed(1),
    }
    historyRef.current = [...historyRef.current.slice(-30), entry]
  }

  if (loading && !data) return <LoadingState message="Connecting to ISP Observability API…" />
  if (error) return <ErrorState message={error} />

  const t  = data?.telemetry  || {}
  const a  = data?.analysis   || {}
  const hist = historyRef.current

  return (
    <div className="fade-in">
      {/* ── Header ─────────────────────────────────────── */}
      <div className="page-header">
        <h1 className="page-title">
          <span className="status-dot live" />
          Network Operations Center
        </h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 8 }}>
          <p className="page-subtitle">Real-time ISP network telemetry and AI-powered analysis</p>
          {a.severity && <SeverityBadge severity={a.severity} />}
          {a.qoe_class && <QoEBadge qoeClass={a.qoe_class} />}
        </div>
      </div>

      {/* ── Top stat cards ───────────────────────────── */}
      <div className="grid-4" style={{ marginBottom: 20 }}>
        <MetricCard
          title="Network Latency"
          value={t.latency_ms?.toFixed(1)}
          unit="ms"
          status={getLatencyStatus(t.latency_ms)}
          icon={Activity}
        />
        <MetricCard
          title="Packet Loss"
          value={t.packet_loss_percent?.toFixed(2)}
          unit="%"
          status={getPacketLossStatus(t.packet_loss_percent)}
          icon={AlertTriangle}
        />
        <MetricCard
          title="Throughput"
          value={t.throughput_mbps?.toFixed(1)}
          unit="Mbps"
          status={getTpStatus(t.throughput_mbps)}
          icon={Wifi}
        />
        <MetricCard
          title="Bandwidth Util."
          value={t.bandwidth_utilization_percent?.toFixed(1)}
          unit="%"
          status={getBwStatus(t.bandwidth_utilization_percent)}
          icon={Activity}
        />
      </div>

      <div className="grid-4" style={{ marginBottom: 20 }}>
        <MetricCard
          title="Jitter"
          value={t.jitter_ms?.toFixed(1)}
          unit="ms"
          status={t.jitter_ms > 35 ? 'crit' : t.jitter_ms > 20 ? 'warn' : 'good'}
        />
        <MetricCard
          title="Router CPU"
          value={t.router_cpu_percent?.toFixed(1)}
          unit="%"
          status={t.router_cpu_percent > 90 ? 'crit' : t.router_cpu_percent > 80 ? 'warn' : 'good'}
          icon={Cpu}
        />
        <MetricCard
          title="Router Memory"
          value={t.router_memory_percent?.toFixed(1)}
          unit="%"
          status={t.router_memory_percent > 88 ? 'crit' : t.router_memory_percent > 78 ? 'warn' : 'good'}
        />
        <MetricCard
          title="Active Connections"
          value={t.active_connections?.toLocaleString()}
          unit=""
          status="info"
          icon={Wifi}
        />
      </div>

      {/* ── AI health score ───────────────────────────── */}
      <div className="grid-3" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-title">AI Health Score</div>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12 }}>
            <span className={`stat-value ${a.health_score >= 70 ? 'text-good' : a.health_score >= 40 ? 'text-warn' : 'text-crit'}`}>
              {a.health_score?.toFixed(0) ?? '—'}
            </span>
            <span style={{ color: 'var(--text-muted)', marginBottom: 4 }}>/ 100</span>
          </div>
          {a.severity && <SeverityBadge severity={a.severity} />}
        </div>

        <div className="card">
          <div className="card-title">Anomaly Detection</div>
          <div className="stat-value" style={{ color: a.is_anomaly ? 'var(--status-crit)' : 'var(--status-good)' }}>
            {a.is_anomaly ? 'ANOMALY' : 'NORMAL'}
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: 4 }}>
            Score: {a.anomaly_score?.toFixed(4) ?? '—'}
          </div>
        </div>

        <div className="card">
          <div className="card-title">Customer QoE</div>
          <div className="stat-value" style={{ color: { GOOD: 'var(--status-good)', MODERATE: 'var(--status-warn)', POOR: 'var(--status-crit)' }[a.qoe_class] || 'var(--text-primary)' }}>
            {a.qoe_class ?? '—'}
          </div>
          {a.class_probabilities && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
              {Object.entries(a.class_probabilities).map(([k, v]) => (
                <span key={k} style={{ marginRight: 8 }}>{k}: {(v * 100).toFixed(0)}%</span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Charts ──────────────────────────────────── */}
      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Latency &amp; Jitter (ms)</div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={hist}>
              <defs>
                <linearGradient id="latencyGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.08)" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#475569' }} />
              <YAxis tick={{ fontSize: 10, fill: '#475569' }} unit="ms" />
              <Tooltip contentStyle={{ background: '#131d35', border: '1px solid #38bdf820', fontSize: 12 }} />
              <Legend iconType="line" wrapperStyle={{ fontSize: 12 }} />
              <Area type="monotone" dataKey="latency" stroke="#38bdf8" fill="url(#latencyGrad)" name="Latency" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Packet Loss &amp; Bandwidth (%)</div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={hist}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.08)" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#475569' }} />
              <YAxis tick={{ fontSize: 10, fill: '#475569' }} unit="%" />
              <Tooltip contentStyle={{ background: '#131d35', border: '1px solid #38bdf820', fontSize: 12 }} />
              <Legend iconType="line" wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="packet"    stroke="#ef4444" name="Packet Loss" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="bandwidth" stroke="#f59e0b" name="Bandwidth"   dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Throughput (Mbps)</div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={hist}>
              <defs>
                <linearGradient id="tpGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.08)" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#475569' }} />
              <YAxis tick={{ fontSize: 10, fill: '#475569' }} unit=" Mbps" />
              <Tooltip contentStyle={{ background: '#131d35', border: '1px solid #38bdf820', fontSize: 12 }} />
              <Area type="monotone" dataKey="throughput" stroke="#22c55e" fill="url(#tpGrad)" name="Throughput" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Router CPU &amp; Memory (%)</div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={hist}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.08)" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#475569' }} />
              <YAxis tick={{ fontSize: 10, fill: '#475569' }} unit="%" />
              <Tooltip contentStyle={{ background: '#131d35', border: '1px solid #38bdf820', fontSize: 12 }} />
              <Legend iconType="line" wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="cpu"    stroke="#8b5cf6" name="CPU"    dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="memory" stroke="#ec4899" name="Memory" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── AI Explanation ───────────────────────────── */}
      {a.explanation && (
        <div className="card fade-in" style={{ marginBottom: 20, borderColor: a.is_anomaly ? 'rgba(239,68,68,0.3)' : 'var(--border)' }}>
          <div className="card-title">🤖 AI Network Insight</div>
          <p style={{ color: 'var(--text-primary)', fontSize: '0.92rem', lineHeight: 1.7, margin: '8px 0' }}>
            {a.explanation}
          </p>
          {a.recommendations?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>INVESTIGATION RECOMMENDATIONS</div>
              <ul style={{ paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 4 }}>
                {a.recommendations.map((r, i) => (
                  <li key={i} style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* ── Current scenario ─────────────────────────── */}
      {t.scenario && (
        <div className="card" style={{ background: 'rgba(56,189,248,0.04)' }}>
          <div className="card-title">Active Simulation Scenario</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span className="badge badge-info">{t.scenario.toUpperCase().replace(/-/g, ' ')}</span>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Uptime: {t.uptime_seconds?.toFixed(0)}s · Network availability: {t.network_availability_percent?.toFixed(2)}%
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
