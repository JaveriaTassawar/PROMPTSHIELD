import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import Badge from '../Badge.jsx'
import Card from '../Card.jsx'
import { BarChartIcon } from '../icons.jsx'

// Attack frequency by class (Task 88). Backend Task 64 defines no time series,
// so outside ?mock=preview this shows that the data isn't available — the chart
// only renders a series the data layer actually supplied.
const SERIES = [
  { key: 'directJailbreak', label: 'Direct Jailbreak', color: 'var(--color-danger)' },
  { key: 'indirectInjection', label: 'Indirect Injection', color: 'var(--color-warning)' },
]

const TICK = { fill: 'var(--color-fg-muted)', fontSize: 12 }

function ChartMessage({ title, text }) {
  return (
    <div className="flex h-64 flex-col items-center justify-center gap-3 rounded-control border border-dashed border-border px-6 text-center">
      <span className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-surface-raised text-fg-subtle">
        <BarChartIcon className="h-5 w-5" />
      </span>
      <p className="font-medium text-fg">{title}</p>
      <p className="max-w-sm text-sm text-fg-muted">{text}</p>
    </div>
  )
}

function AttackFrequencyChart({ frequency, loading = false, sample = false }) {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  let body
  if (loading) {
    body = (
      <div className="h-64 animate-pulse rounded-control bg-surface-raised/60">
        <span className="sr-only">Loading attack frequency</span>
      </div>
    )
  } else if (frequency == null) {
    body = (
      <ChartMessage
        title="Frequency data is not available yet"
        text="PromptShield’s dashboard API does not provide attack counts over time yet, so there is nothing to chart."
      />
    )
  } else if (frequency.length === 0) {
    body = <ChartMessage title="No attacks recorded yet" text="Attack frequency will appear here once attacks are detected." />
  } else {
    body = (
      <figure>
        <div className="h-64" aria-hidden="true">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={frequency} margin={{ top: 8, right: 8, bottom: 0, left: -16 }} barGap={4}>
              <CartesianGrid vertical={false} stroke="var(--color-border)" strokeDasharray="3 3" />
              <XAxis dataKey="point" tick={TICK} tickLine={false} axisLine={{ stroke: 'var(--color-border)' }} />
              <YAxis allowDecimals={false} tick={TICK} tickLine={false} axisLine={false} />
              <Tooltip
                cursor={{ fill: 'var(--color-surface-raised)', opacity: 0.6 }}
                contentStyle={{
                  background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 8,
                  fontSize: 12,
                }}
                labelStyle={{ color: 'var(--color-fg)', fontWeight: 600 }}
              />
              {SERIES.map((series) => (
                <Bar
                  key={series.key}
                  dataKey={series.key}
                  name={series.label}
                  fill={series.color}
                  radius={[4, 4, 0, 0]}
                  maxBarSize={28}
                  isAnimationActive={!reduceMotion}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
        <figcaption className="sr-only">
          <table>
            <caption>Attack frequency{sample ? ' (sample data, not real)' : ''}</caption>
            <thead>
              <tr>
                <th scope="col">Point</th>
                {SERIES.map((series) => (
                  <th key={series.key} scope="col">
                    {series.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {frequency.map((row) => (
                <tr key={row.point}>
                  <th scope="row">{row.point}</th>
                  {SERIES.map((series) => (
                    <td key={series.key}>{row[series.key]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </figcaption>
      </figure>
    )
  }

  return (
    <Card className="p-5">
      <section aria-labelledby="frequency-heading" className="flex flex-col gap-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 id="frequency-heading" className="font-semibold text-fg">
                Attack frequency
              </h2>
              {sample && <Badge variant="info">Sample</Badge>}
            </div>
            <p className="mt-0.5 text-sm text-fg-muted">
              {sample ? 'Synthetic sample series — not a real time period' : 'Direct Jailbreak and Indirect Injection detections'}
            </p>
          </div>
          <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-fg-muted" aria-label="Chart legend">
            {SERIES.map((series) => (
              <li key={series.key} className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-sm" style={{ background: series.color }} aria-hidden="true" />
                {series.label}
              </li>
            ))}
          </ul>
        </div>
        {body}
      </section>
    </Card>
  )
}

export default AttackFrequencyChart
