import Card from '../Card.jsx'
import ProgressBar from '../ProgressBar.jsx'

// Progress derived only from modules the user has marked complete. XP is
// required by Task 87 but no XP rule exists, so it is shown as not tracked —
// never as a number.
function LearningProgressSummary({ completed, total }) {
  const valueText = `${completed} of ${total} modules completed`

  return (
    <Card className="grid gap-5 p-5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:gap-8">
      <ProgressBar label="Your progress" value={completed} max={total} valueText={valueText} />
      <div className="border-t border-border/70 pt-4 sm:border-t-0 sm:border-l sm:pt-0 sm:pl-8">
        <p className="font-mono text-[11px] tracking-widest text-fg-subtle uppercase">XP</p>
        <p className="mt-1 text-sm font-medium text-fg-muted">Not tracked yet</p>
        <p className="text-xs text-fg-subtle">Unavailable in local preview</p>
      </div>
    </Card>
  )
}

export default LearningProgressSummary
