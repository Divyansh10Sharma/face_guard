import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null

  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-title">{label}</div>
      {payload.map((entry) => (
        <div key={entry.name} className="chart-tooltip-row">
          <span className="chart-tooltip-dot" style={{ background: entry.color }} />
          <span className="chart-tooltip-name">{entry.name}</span>
          <span className="chart-tooltip-value" style={{ color: entry.color }}>
            {typeof entry.value === 'number' && entry.value % 1 !== 0
              ? entry.value.toFixed(2)
              : entry.value}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function TrendChart({ sessions, onSelect }) {
  const data = sessions.map((s) => ({
    name: s.label,
    Frustrated: s.frustrated_alerts,
    'Face Touch': s.face_touch_alerts,
    Squinting: s.squint_alerts,
    'Low Blink': s.low_blink_alerts,
    'Per Min': parseFloat(s.alerts_per_min.toFixed(2)),
    session: s,
  }))

  const handleClick = (data) => {
    if (data && data.activePayload && data.activePayload[0]) {
      const session = data.activePayload[0].payload.session
      if (session && onSelect) onSelect(session)
    }
  }

  return (
    <div className="trend-chart">
      <div className="section-header">
        <span className="section-title">Alert Trends</span>
        <span className="section-subtitle">Click a bar to inspect session events</span>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart
          data={data}
          margin={{ top: 10, right: 24, left: 0, bottom: 0 }}
          onClick={handleClick}
          style={{ cursor: 'pointer' }}
        >
          <CartesianGrid stroke="#1e2d47" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fill: '#64748b', fontSize: 12 }}
            axisLine={{ stroke: '#1e2d47' }}
            tickLine={false}
          />
          <YAxis
            yAxisId="left"
            tick={{ fill: '#64748b', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            width={32}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fill: '#64748b', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            width={40}
            label={{
              value: '/min',
              position: 'insideTopRight',
              fill: '#64748b',
              fontSize: 11,
              offset: 6,
            }}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: '#1e2d4730' }} />
          <Legend
            wrapperStyle={{ color: '#64748b', fontSize: 12, paddingTop: 8 }}
          />
          <Bar yAxisId="left" dataKey="Frustrated" stackId="a" fill="#f59e0b" radius={[0, 0, 0, 0]} />
          <Bar yAxisId="left" dataKey="Face Touch" stackId="a" fill="#ef4444" radius={[0, 0, 0, 0]} />
          <Bar yAxisId="left" dataKey="Squinting" stackId="a" fill="#3b82f6" radius={[0, 0, 0, 0]} />
          <Bar yAxisId="left" dataKey="Low Blink" stackId="a" fill="#a855f7" radius={[4, 4, 0, 0]} />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="Per Min"
            stroke="#10b981"
            strokeWidth={2.5}
            dot={{ fill: '#10b981', r: 3, strokeWidth: 0 }}
            activeDot={{ r: 5, strokeWidth: 0 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
