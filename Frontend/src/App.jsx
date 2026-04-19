import { useState, useEffect, useMemo, useCallback } from 'react'
import './App.css'
import StatCard from './components/StatCard'
import HabitScore from './components/HabitScore'
import TrendChart from './components/TrendChart'
import SessionList from './components/SessionList'
import EventTimeline from './components/EventTimeline'

// ── Data helpers ──────────────────────────────────────────────────────────────

function parseDuration(str) {
  if (!str) return 0
  const mMatch = str.match(/(\d+)m/)
  const sMatch = str.match(/(\d+)s/)
  const minutes = mMatch ? parseInt(mMatch[1], 10) : 0
  const seconds = sMatch ? parseInt(sMatch[1], 10) : 0
  return minutes * 60 + seconds
}

function countByType(events, type) {
  if (!Array.isArray(events)) return 0
  return events.filter((e) => e.type === type).length
}

function avg(arr) {
  if (!arr.length) return 0
  return arr.reduce((a, b) => a + b, 0) / arr.length
}

function enrichSession(session, index) {
  const duration_secs = parseDuration(session.duration)
  const low_blink_alerts = countByType(session.events, 'low_blink')
  const total_alerts =
    (session.frustrated_alerts || 0) +
    (session.face_touch_alerts || 0) +
    (session.squint_alerts || 0) +
    low_blink_alerts
  const alerts_per_min = duration_secs > 0 ? (total_alerts / duration_secs) * 60 : 0

  return {
    ...session,
    index,
    low_blink_alerts,
    total_alerts,
    alerts_per_min,
    duration_secs,
    label: `S${index + 1}`,
  }
}

// ── App ───────────────────────────────────────────────────────────────────────

export default function App() {
  const [sessions, setSessions] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)
  const [spinning, setSpinning] = useState(false)

  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch('/api/sessions')
      const raw = await res.json()
      const enriched = Array.isArray(raw) ? raw.map(enrichSession) : []
      setSessions(enriched)
      setSelected((prev) => {
        if (!prev && enriched.length > 0) return enriched[enriched.length - 1]
        if (prev) {
          const updated = enriched.find((s) => s.label === prev.label)
          return updated || enriched[enriched.length - 1] || null
        }
        return null
      })
    } catch (err) {
      console.error('Failed to fetch sessions:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions, refreshKey])

  useEffect(() => {
    const id = setInterval(() => {
      setRefreshKey((k) => k + 1)
    }, 30000)
    return () => clearInterval(id)
  }, [])

  const handleRefresh = () => {
    setSpinning(true)
    setRefreshKey((k) => k + 1)
    setTimeout(() => setSpinning(false), 800)
  }

  // ── Habit score (first half vs second half by alerts/min) ──────────────────
  const habitScore = useMemo(() => {
    if (sessions.length < 2) return null
    const half = Math.ceil(sessions.length / 2)
    const earlyAvg = avg(sessions.slice(0, half).map((s) => s.alerts_per_min))
    const recentAvg = avg(sessions.slice(half).map((s) => s.alerts_per_min))
    if (earlyAvg === 0) return 0
    return ((earlyAvg - recentAvg) / earlyAvg) * 100
  }, [sessions])

  // ── Totals across all sessions ─────────────────────────────────────────────
  const totals = useMemo(() => {
    return {
      frustrated: sessions.reduce((a, s) => a + s.frustrated_alerts, 0),
      face_touch: sessions.reduce((a, s) => a + s.face_touch_alerts, 0),
      squint: sessions.reduce((a, s) => a + s.squint_alerts, 0),
      low_blink: sessions.reduce((a, s) => a + s.low_blink_alerts, 0),
    }
  }, [sessions])

  const maxStat = Math.max(totals.frustrated, totals.face_touch, totals.squint, totals.low_blink, 1)

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p>Loading FaceGuard data…</p>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">🛡️</span>
            <div>
              <div className="logo-title">FaceGuard</div>
              <div className="logo-subtitle">Habit & Alert Dashboard</div>
            </div>
          </div>
        </div>
        <div className="header-right">
          <HabitScore score={habitScore} />
          <button
            className={`refresh-btn${spinning ? ' refresh-btn--spinning' : ''}`}
            onClick={handleRefresh}
            title="Refresh data"
          >
            <span className="refresh-icon">↻</span>
            Refresh
          </button>
        </div>
      </header>

      <section className="stats-row">
        <StatCard
          icon="😤"
          value={totals.frustrated}
          label="Frustrated"
          color="#f59e0b"
          maxValue={maxStat}
          animDelay="0s"
        />
        <StatCard
          icon="🤚"
          value={totals.face_touch}
          label="Face Touches"
          color="#ef4444"
          maxValue={maxStat}
          animDelay="0.1s"
        />
        <StatCard
          icon="😑"
          value={totals.squint}
          label="Squinting"
          color="#3b82f6"
          maxValue={maxStat}
          animDelay="0.2s"
        />
        <StatCard
          icon="👁️"
          value={totals.low_blink}
          label="Low Blink"
          color="#a855f7"
          maxValue={maxStat}
          animDelay="0.3s"
        />
      </section>

      {sessions.length > 0 ? (
        <>
          <section className="chart-section">
            <TrendChart sessions={sessions} onSelect={setSelected} />
          </section>

          <section className="bottom-grid">
            <div className="session-panel">
              <SessionList sessions={sessions} selected={selected} onSelect={setSelected} />
            </div>
            <div className="timeline-panel">
              <EventTimeline session={selected} />
            </div>
          </section>
        </>
      ) : (
        <div className="no-data">
          <div className="no-data-icon">📭</div>
          <div className="no-data-title">No session data found</div>
          <div className="no-data-sub">
            Run FaceGuard to record sessions — they'll appear here automatically.
          </div>
        </div>
      )}
    </div>
  )
}
