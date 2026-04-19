import { useEffect, useState } from 'react'

const RADIUS = 40
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

export default function HabitScore({ score }) {
  const [offset, setOffset] = useState(CIRCUMFERENCE)

  useEffect(() => {
    if (score === null) return
    const clampedAbs = Math.min(Math.abs(score), 100)
    const targetOffset = CIRCUMFERENCE - (clampedAbs / 100) * CIRCUMFERENCE

    let frame
    const start = Date.now()
    const animate = () => {
      const p = Math.min((Date.now() - start) / 1000, 1)
      const eased = 1 - Math.pow(1 - p, 3)
      const current = CIRCUMFERENCE - eased * (CIRCUMFERENCE - targetOffset)
      setOffset(current)
      if (p < 1) frame = requestAnimationFrame(animate)
    }
    frame = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frame)
  }, [score])

  if (score === null) {
    return (
      <div className="habit-score habit-score--empty">
        <div className="habit-score-hint">Need 2+ sessions</div>
      </div>
    )
  }

  const improving = score >= 0
  const ringColor = improving ? '#10b981' : '#ef4444'
  const absScore = Math.abs(score)

  return (
    <div className="habit-score">
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r={RADIUS}
          fill="none"
          stroke="#1e2d47"
          strokeWidth="8"
        />
        <circle
          cx="50"
          cy="50"
          r={RADIUS}
          fill="none"
          stroke={ringColor}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
          style={{ transition: 'stroke 0.3s ease' }}
        />
        <text
          x="50"
          y="46"
          textAnchor="middle"
          dominantBaseline="middle"
          fill={ringColor}
          fontSize="13"
          fontWeight="700"
          fontFamily="Inter, sans-serif"
        >
          {improving ? '+' : '-'}{absScore.toFixed(0)}%
        </text>
        <text
          x="50"
          y="62"
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#64748b"
          fontSize="7"
          fontWeight="500"
          fontFamily="Inter, sans-serif"
          letterSpacing="0.5"
        >
          {improving ? 'IMPROVING' : 'NEEDS WORK'}
        </text>
      </svg>
    </div>
  )
}
