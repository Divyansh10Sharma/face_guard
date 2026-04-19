import { useState, useEffect } from 'react'

export default function StatCard({ icon, value, label, color, maxValue, animDelay = '0s' }) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    let frame
    const start = Date.now()
    const animate = () => {
      const p = Math.min((Date.now() - start) / 1200, 1)
      const eased = 1 - Math.pow(1 - p, 3)
      setCount(Math.round(eased * value))
      if (p < 1) frame = requestAnimationFrame(animate)
    }
    frame = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frame)
  }, [value])

  const barWidth = maxValue > 0 ? Math.min((value / maxValue) * 100, 100) : 0

  return (
    <div className="stat-card" style={{ '--accent': color, animationDelay: animDelay }}>
      <div className="stat-card-top-bar" />
      <div className="stat-card-inner">
        <div className="stat-icon">{icon}</div>
        <div className="stat-number" style={{ color }}>{count}</div>
        <div className="stat-label">{label}</div>
        <div className="stat-bar-track">
          <div
            className="stat-bar-fill"
            style={{ width: `${barWidth}%`, background: color }}
          />
        </div>
      </div>
    </div>
  )
}
