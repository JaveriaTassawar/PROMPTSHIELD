import Spinner from './Spinner.jsx'

// Shared page-level loading presentation: a labelled spinner above a faint
// skeleton of the page. Visual only — callers decide when to show it.
function PageLoading({ label }) {
  return (
    <div className="flex flex-col gap-6">
      <p role="status" className="flex items-center gap-2.5 text-sm text-fg-muted">
        <Spinner className="h-4 w-4 text-accent" />
        {label}
      </p>
      <div className="flex flex-col gap-4" aria-hidden="true">
        <span className="h-8 w-2/3 max-w-sm animate-shimmer rounded-control bg-surface-raised" />
        <span className="h-4 w-full max-w-xl animate-shimmer rounded bg-surface-raised" style={{ animationDelay: '150ms' }} />
        <span className="glass h-40 animate-shimmer rounded-card border border-border/60" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  )
}

export default PageLoading
