export default function SessionList({ sessions, selected, onSelect }) {
  const alertTypes = [
    { key: 'frustrated_alerts', emoji: '😤', color: '#f59e0b' },
    { key: 'face_touch_alerts', emoji: '🤚', color: '#ef4444' },
    { key: 'squint_alerts', emoji: '😑', color: '#3b82f6' },
    { key: 'low_blink_alerts', emoji: '👁️', color: '#a855f7' },
  ]

  return (
    <div className="session-list">
      <div className="section-header">
        <span className="section-title">Sessions</span>
        <span className="section-subtitle">{sessions.length} recorded</span>
      </div>
      <div className="session-scroll">
        {sessions.length === 0 && (
          <div className="session-empty">No sessions yet</div>
        )}
        {sessions.map((s) => {
          const isActive = selected && selected.label === s.label
          return (
            <div
              key={s.label}
              className={`session-card${isActive ? ' session-card--active' : ''}`}
              onClick={() => onSelect(s)}
            >
              <div className="session-card-header">
                <span className="session-badge">#{s.index + 1}</span>
                <span className="session-time">{s.start_time}</span>
                <span className="session-duration">{s.duration}</span>
              </div>
              <div className="session-badges">
                {alertTypes.map(({ key, emoji, color }) =>
                  s[key] > 0 ? (
                    <span
                      key={key}
                      className="alert-badge"
                      style={{
                        background: `${color}20`,
                        color: color,
                        border: `1px solid ${color}40`,
                      }}
                    >
                      {emoji} {s[key]}
                    </span>
                  ) : null
                )}
              </div>
              <div className="session-card-footer">
                <span className="session-total">{s.total_alerts} alerts total</span>
                <span className="session-rate">{s.alerts_per_min.toFixed(1)}/min</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
