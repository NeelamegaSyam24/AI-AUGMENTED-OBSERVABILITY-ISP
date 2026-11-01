import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Activity, AlertTriangle, Wifi, List, Sliders, ExternalLink } from 'lucide-react'
import './styles/app.css'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const AnomalyPage = lazy(() => import('./pages/AnomalyPage'))
const QoEPage = lazy(() => import('./pages/QoEPage'))
const EventsPage = lazy(() => import('./pages/EventsPage'))
const ScenarioPage = lazy(() => import('./pages/ScenarioPage'))

const NAV_LINKS = [
  { to: '/',          label: 'Dashboard',  Icon: Activity },
  { to: '/anomalies', label: 'Anomalies',  Icon: AlertTriangle },
  { to: '/qoe',       label: 'QoE',        Icon: Wifi },
  { to: '/events',    label: 'Events',     Icon: List },
  { to: '/scenarios', label: 'Scenarios',  Icon: Sliders },
]

const GRAFANA_URL = import.meta.env.VITE_GRAFANA_URL || (import.meta.env.DEV ? 'http://localhost:3000' : '')
const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '')
const EXT_LINKS = [
  ...(GRAFANA_URL ? [{ href: GRAFANA_URL, label: 'Grafana' }] : []),
  ...(API_URL ? [{ href: `${API_URL}/docs`, label: 'API Docs' }] : []),
]

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        {/* ── Sidebar ─────────────────────────────────── */}
        <aside className="sidebar">
          <div className="sidebar-brand">
            <div className="brand-icon">
              <Activity size={22} color="#38bdf8" />
            </div>
            <div className="brand-text">
              <span className="brand-title">ISP Observer</span>
              <span className="brand-sub">AI-Augmented NOC</span>
            </div>
          </div>

          <nav className="sidebar-nav">
            <div className="nav-section-label">Main</div>
            {NAV_LINKS.map(({ to, label, Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <Icon size={18} />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>

          <div className="sidebar-footer">
            <div className="nav-section-label">External Tools</div>
            {EXT_LINKS.map(({ href, label }) => (
              <a key={href} href={href} target="_blank" rel="noopener noreferrer" className="ext-link">
                <ExternalLink size={14} />
                {label}
              </a>
            ))}
            <div className="version-tag">v1.0.0 · Academic Project</div>
          </div>
        </aside>

        {/* ── Main content ─────────────────────────────── */}
        <main className="main-content">
          <Suspense fallback={<div className="card">Loading page...</div>}>
            <Routes>
              <Route path="/"          element={<Dashboard />} />
              <Route path="/anomalies" element={<AnomalyPage />} />
              <Route path="/qoe"       element={<QoEPage />} />
              <Route path="/events"    element={<EventsPage />} />
              <Route path="/scenarios" element={<ScenarioPage />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </BrowserRouter>
  )
}
