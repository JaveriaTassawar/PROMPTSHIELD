// App-wide build status: this frontend runs on local mocks until the backend
// is wired. Deliberately secondary and neutral — it is a disclosure, not an error.
function PreviewStatus({ compact = false, className = '' }) {
  return (
    <p
      className={`inline-flex items-center gap-2 rounded-full border border-border/70 bg-surface/60 font-mono tracking-wide text-fg-muted ${
        compact ? 'px-2.5 py-1 text-[10px]' : 'px-3 py-1.5 text-[11px]'
      } ${className}`}
    >
      <span className="relative flex h-2 w-2 shrink-0" aria-hidden="true">
        <span className="absolute inset-0 animate-breathe rounded-full bg-accent/40" />
        <span className="relative m-auto h-1.5 w-1.5 rounded-full bg-accent" />
      </span>
      {compact ? 'Local preview' : 'Local preview · backend not connected'}
    </p>
  )
}

export default PreviewStatus
