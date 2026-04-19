const TYPE_META = {
  frustrated: { color: '#f59e0b', emoji: '😤', label: 'Frustrated' },
  face_touch: { color: '#ef4444', emoji: '🤚', label: 'Face Touch' },
  squint: { color: '#3b82f6', emoji: '😑', label: 'Squinting' },
  low_blink: { color: '#a855f7', emoji: '👁️', label: 'Low Blink' },
}

function getMeta(type) {
  return TYPE_META[type] || { color: '#64748b', emoji: '❓', label: type }
}

export default function EventTimeline({ session }) {
  if (!session) {
    return (
      <div className="event-timeline">
        <div className="section-header">
          <span className="section-title">Event Timeline</span>
        </div>
        <div className="timeline-empty">Select a session to view events</div>
      </div>
    )
  }

  const events = session.events || []

  if (events.length === 0) {
    return (
      <div className="event-timeline">
        <div className="section-header">
          <span className="section-title">Event Timeline</span>
          <span className="section-subtitle">{session.label} — {session.date}</span>
        </div>
        <div className="timeline-empty">No events in this session 🎉</div>
      </div>
    )
  }

  const timestamps = events.map((e) => e.timestamp)
  const minTs = Math.min(...timestamps)
  const maxTs = Math.max(...timestamps)
  const totalSecs = maxTs - minTs || 1

  return (
    <div className="event-timeline">
      <div className="section-header">
        <span className="section-title">Event Timeline</span>
        <span className="section-subtitle">{session.label} — {session.date}</span>
      </div>

      <div className="timeline-legend">
        {Object.entries(TYPE_META).map(([type, meta]) => (
          <span key={type} className="legend-item">
            <span className="legend-dot" style={{ background: meta.color }} />
            {meta.label}
          </span>
        ))}
      </div>

      <div className="timeline-track-wrapper">
        <div className="timeline-track">
          {events.map((event, i) => {
            const meta = getMeta(event.type)
            const offsetSecs = event.timestamp - minTs
            const leftPct = (offsetSecs / totalSecs) * 100
            return (
              <div
                key={i}
                className="timeline-dot-wrapper"
                style={{ left: `${leftPct}%` }}
              >
                <span className="timeline-dot" style={{ color: meta.color }}>
                  {meta.emoji}
                </span>
                <div className="timeline-tooltip">
                  <span style={{ color: meta.color }}>{meta.label}</span>
                  <span className="timeline-tooltip-time">{event.time}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="event-log">
        {events.map((event, i) => {
          const meta = getMeta(event.type)
          return (
            <div key={i} className="event-log-row">
              <span className="event-log-time">{event.time}</span>
              <span className="event-log-dot" style={{ background: meta.color }} />
              <span className="event-log-label">
                {meta.emoji} {meta.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
