import { Link } from 'react-router-dom'
import Card from '../Card.jsx'
import { findDetectionClass } from '../../config/detection.js'
import { ArrowRightIcon, CheckIcon } from '../icons.jsx'

// End of the walkthrough. States only facts already on screen (turn count and
// which turns were flagged by the scenario annotations) — scoring and results
// belong to Task 86.
function CompletionPanel({ scenario, entries, headingRef, onRestart }) {
  const flagged = entries
    .map((entry, index) => ({ number: index + 1, detection: entry.detection }))
    .filter(({ detection }) => detection.classification !== 'Safe')

  return (
    <Card borderClassName="border-accent/30" className="animate-fade-up p-5">
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 animate-scale-in items-center justify-center rounded-full bg-primary text-white">
          <CheckIcon className="h-5 w-5" strokeWidth="2.5" />
        </span>
        <div className="min-w-0">
          <h2 ref={headingRef} tabIndex={-1} className="rounded text-lg font-semibold text-fg">
            Scenario complete
          </h2>
          <p className="mt-1 text-sm text-fg-muted">
            You sent all {entries.length} turns of {scenario.code} · {scenario.title}.
          </p>
          {flagged.length > 0 && (
            <ul className="mt-2 flex flex-col gap-1 text-sm text-fg-muted">
              {flagged.map(({ number, detection }) => (
                <li key={number}>
                  Turn {number} was annotated as{' '}
                  <span className="font-medium text-fg">
                    {findDetectionClass(detection.classification).label}
                    {detection.subtype && ` · ${detection.subtype}`}
                  </span>
                  .
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      <div className="mt-5 flex flex-col-reverse gap-3 border-t border-border/70 pt-4 sm:flex-row sm:items-center sm:justify-between">
        <button
          type="button"
          onClick={onRestart}
          className="rounded-control px-4 py-2.5 text-sm font-semibold text-fg-muted transition-colors hover:bg-surface-raised hover:text-fg"
        >
          Restart scenario
        </button>
        <Link
          to={`/simulation/${scenario.id}/results`}
          state={{ run: { scenarioId: scenario.id, entries } }}
          className="inline-flex items-center justify-center gap-2 rounded-control bg-linear-to-r from-primary to-indigo px-4 py-2.5 font-semibold text-white shadow-glow transition duration-150 ease-snappy hover:-translate-y-px hover:shadow-glow-strong active:translate-y-0"
        >
          View Results
          <ArrowRightIcon className="h-4.5 w-4.5" />
        </Link>
      </div>
    </Card>
  )
}

export default CompletionPanel
