// frontend/src/pages/QoEPage.jsx
import React, { useCallback, useRef } from 'react'
import { Wifi } from 'lucide-react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend } from 'recharts'
import { usePoll } from '../hooks/useApi'
import { api } from '../services/api'
import { QoEBadge, LoadingState, ErrorState } from '../components/MetricCard'

const QOE_COLORS = { GOOD: '#22c55e', MODERATE: '#f59e0b', POOR: '#ef4444' }

export default function QoEPage() {
  const fetcher  = useCallback(() => api.predictions(100), [])
  const { data, loading, error } = usePoll(fetcher, 8000)

  const qoeFetcher = useCallback(() => api.qoe(), [])
  const { data: qoeData } = usePoll(qoeFetcher, 8000)

  const modelFetcher = useCallback(() => api.modelInfo(), [])
  const { data: modelInfo } = usePoll(modelFetcher, 60000)

  if (loading && !data) return <LoadingState />
  if (error) return <ErrorState message={error} />

  const preds = data?.predictions || []

  // Build distribution
  const dist = { GOOD: 0, MODERATE: 0, POOR: 0 }
  preds.forEach(p => { if (p.qoe?.qoe_class in dist) dist[p.qoe.qoe_class]++ })
  const pieData = Object.entries(dist).map(([name, value]) => ({ name, value }))

  // Build trend (last 30)
  const trend = preds.slice(0, 30).reverse().map((p, i) => ({
    i,
    time: new Date(p.timestamp).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    score: p.qoe?.qoe_score ?? 0,
    qoe: p.qoe?.qoe_class,
  }))

  const meta = modelInfo?.metadata || {}
  const report = meta.qoe_report || {}
  const classes = ['GOOD', 'MODERATE', 'POOR']

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title"><Wifi size={24} /> Quality of Experience</h1>
        <p className="page-subtitle">
          Customer QoE estimation using Random Forest classification
        </p>
      </div>

      {/* ── Current QoE ─────────────────────────────── */}
      <div className="grid-3" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-title">Current QoE</div>
          <div className="stat-value" style={{ color: QOE_COLORS[qoeData?.qoe_class] || 'var(--text-primary)' }}>
            {qoeData?.qoe_class ?? '—'}
          </div>
          {qoeData?.class_probabilities && (
            <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
              {Object.entries(qoeData.class_probabilities).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.82rem' }}>
                  <span style={{ color: 'var(--text-muted)', width: 70 }}>{k}</span>
                  <div style={{ flex: 1, height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ width: `${(v * 100).toFixed(0)}%`, height: '100%', background: QOE_COLORS[k], transition: 'width 0.5s' }} />
                  </div>
                  <span style={{ color: 'var(--text-secondary)', width: 36, textAlign: 'right' }}>{(v * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pie chart */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-title" style={{ marginBottom: 8 }}>QoE Distribution (last {preds.length} predictions)</div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <ResponsiveContainer width={220} height={180}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label={({ name, value }) => `${name}: ${value}`} labelLine={false} fontSize={11}>
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={QOE_COLORS[entry.name]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#131d35', border: '1px solid #38bdf820', fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ flex: 1 }}>
              {pieData.map(({ name, value }) => (
                <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                  <div style={{ width: 12, height: 12, borderRadius: 3, background: QOE_COLORS[name] }} />
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>{name}</span>
                  <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── QoE Trend ───────────────────────────────── */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-title" style={{ marginBottom: 12 }}>QoE Score Trend (0=POOR · 1=MODERATE · 2=GOOD)</div>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={trend}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.08)" />
            <XAxis dataKey="time" tick={{ fontSize: 9, fill: '#475569' }} />
            <YAxis domain={[0, 2]} ticks={[0, 1, 2]} tick={{ fontSize: 10, fill: '#475569' }} />
            <Tooltip
              contentStyle={{ background: '#131d35', border: '1px solid #38bdf820', fontSize: 12 }}
              formatter={(v) => [['POOR', 'MODERATE', 'GOOD'][v], 'QoE']}
            />
            <Bar dataKey="score" name="QoE Score" radius={[3, 3, 0, 0]}>
              {trend.map((entry, i) => (
                <Cell key={i} fill={QOE_COLORS[entry.qoe] || '#475569'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ── Model metadata ───────────────────────────── */}
      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-title">Model Configuration</div>
          <dl style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px', marginTop: 8 }}>
            <dt style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>Algorithm</dt>
            <dd style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>Random Forest</dd>
            <dt style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>Training Samples</dt>
            <dd style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>{meta.training_samples ?? '—'}</dd>
            <dt style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>Overall Accuracy</dt>
            <dd style={{ color: 'var(--status-good)', fontSize: '0.88rem', fontWeight: 600 }}>
              {meta.qoe_accuracy ? (meta.qoe_accuracy * 100).toFixed(2) + '%' : '—'}
            </dd>
            <dt style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>Classes</dt>
            <dd style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>GOOD · MODERATE · POOR</dd>
          </dl>
        </div>

        <div className="card">
          <div className="card-title">QoE Label Methodology (Synthetic)</div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.7, marginTop: 6 }}>
            {Object.entries(meta.qoe_label_rules || {
              'GOOD': 'latency_ms < 60 AND packet_loss < 1% AND bandwidth_util < 75%',
              'POOR': 'latency_ms > 130 OR packet_loss > 5% OR bandwidth_util > 90%',
              'MODERATE': 'All other observations',
            }).map(([cls, rule]) => (
              <div key={cls} style={{ marginBottom: 6 }}>
                <span className={`badge ${cls === 'GOOD' ? 'badge-good' : cls === 'POOR' ? 'badge-crit' : 'badge-warn'}`} style={{ marginRight: 8 }}>{cls}</span>
                <code style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{rule}</code>
              </div>
            ))}
            <p style={{ color: 'var(--text-muted)', fontSize: '0.78rem', marginTop: 8 }}>
              ⚠️ Labels are synthetic and rule-based. The classifier learns to generalise these rules —
              it does NOT directly measure subjective customer satisfaction.
            </p>
          </div>
        </div>
      </div>

      {/* ── Evaluation metrics table ─────────────────── */}
      {Object.keys(report).length > 0 && (
        <div className="card">
          <div className="card-title" style={{ marginBottom: 12 }}>Classification Report</div>
          <table className="data-table">
            <thead>
              <tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1-Score</th><th>Support</th></tr>
            </thead>
            <tbody>
              {classes.map(cls => {
                const r = report[cls] || {}
                return (
                  <tr key={cls}>
                    <td><QoEBadge qoeClass={cls} /></td>
                    <td>{r.precision?.toFixed(4) ?? '—'}</td>
                    <td>{r.recall?.toFixed(4) ?? '—'}</td>
                    <td>{r['f1-score']?.toFixed(4) ?? '—'}</td>
                    <td>{r.support ?? '—'}</td>
                  </tr>
                )
              })}
              <tr style={{ borderTop: '1px solid var(--border-active)' }}>
                <td style={{ fontWeight: 600 }}>Overall Accuracy</td>
                <td colSpan={4} style={{ color: 'var(--status-good)', fontWeight: 600 }}>
                  {meta.qoe_accuracy ? (meta.qoe_accuracy * 100).toFixed(2) + '%' : '—'}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
