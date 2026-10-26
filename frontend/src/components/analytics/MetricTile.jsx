import Badge from '../Badge.jsx'
import Card from '../Card.jsx'

// One headline figure. A missing value reads "Not available" with the reason
// in `note` — never a zero or a guess. `sample` marks preview-only values.
function MetricTile({ label, value, note, loading = false, sample = false, valueClassName = 'text-fg' }) {
  return (
    <Card className="flex flex-col gap-1 p-5">
      <div className="flex items-start justify-between gap-2">
        <p className="font-mono text-[11px] tracking-widest text-fg-subtle uppercase">{label}</p>
        {sample && <Badge variant="info">Sample</Badge>}
      </div>
      {loading ? (
        <p className="mt-1 h-8 w-24 animate-pulse rounded-control bg-surface-raised">
          <span className="sr-only">Loading</span>
        </p>
      ) : value == null ? (
        <p className="mt-1 text-lg font-semibold text-fg-muted">Not available</p>
      ) : (
        <p className={`mt-1 text-3xl font-bold tracking-tight tabular-nums ${valueClassName}`}>{value}</p>
      )}
      {note && <p className="text-xs text-fg-subtle">{note}</p>}
    </Card>
  )
}

export default MetricTile
