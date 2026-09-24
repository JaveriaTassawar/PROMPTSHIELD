import Badge from '../Badge.jsx'
import Card from '../Card.jsx'
import DifficultyBadge from './DifficultyBadge.jsx'
import { CheckIcon } from '../icons.jsx'
import { DETECTION_CLASSES, findDetectionClass } from '../../config/detection.js'

// Facts about the completed run only: the scenario, its training difficulty,
// how many turns were sent and how the scenario annotated them. No score,
// pass/fail or performance measure.
function Fact({ label, children }) {
  return (
    <div className="min-w-0 rounded-control border border-border/60 bg-canvas/50 px-3 py-2.5">
      <dt className="font-mono text-[10px] tracking-widest text-fg-subtle uppercase">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-fg">{children}</dd>
    </div>
  )
}

function RunSummary({ scenario, entries }) {
  const counts = DETECTION_CLASSES.map((detection) => ({
    detection,
    count: entries.filter((entry) => entry.detection.classification === detection.label).length,
  })).filter(({ count }) => count > 0)

  const flagged = entries
    .map((entry, index) => ({ number: index + 1, detection: entry.detection }))
    .filter(({ detection }) => detection.classification !== 'Safe')

  return (
    <Card glow className="relative overflow-hidden bg-linear-to-br from-primary/10 via-transparent to-transparent p-5 sm:p-6">
      <section aria-labelledby="run-summary-heading" className="flex flex-col gap-5">
        <div className="flex items-start gap-4">
          <span className="flex h-12 w-12 shrink-0 animate-scale-in items-center justify-center rounded-full bg-linear-to-br from-primary to-indigo text-white shadow-glow sm:h-14 sm:w-14">
            <CheckIcon className="h-6 w-6 sm:h-7 sm:w-7" strokeWidth="2.5" />
          </span>
          <div className="min-w-0">
            <h2 id="run-summary-heading" className="font-mono text-[11px] tracking-widest text-fg-subtle uppercase">
              Run summary
            </h2>
            <p className="mt-1 text-2xl leading-tight font-bold tracking-tight text-fg sm:text-3xl">Scenario complete</p>
            <p className="mt-1 text-sm text-fg-muted">{scenario.title}</p>
          </div>
        </div>

        <dl className="grid gap-3 sm:grid-cols-3">
          <Fact label="Turns sent">
            {entries.length} of {entries.length}
          </Fact>
          <Fact label="Training difficulty">
            <DifficultyBadge difficulty={scenario.difficulty} />
          </Fact>
          <Fact label="Attack pattern">
            <span className="flex flex-wrap items-center gap-2">
              <Badge variant={scenario.detection.variant}>{scenario.detection.label}</Badge>
              <span className="font-mono text-xs text-fg-muted">{scenario.subtype}</span>
            </span>
          </Fact>
        </dl>

        <div className="border-t border-border/70 pt-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-fg-subtle">Scenario annotations:</span>
            {counts.map(({ detection, count }) => (
              <Badge key={detection.label} variant={detection.variant}>
                {detection.label} × {count}
              </Badge>
            ))}
          </div>

          {flagged.length > 0 && (
            <ul className="mt-3 flex flex-col gap-1 text-sm text-fg-muted">
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
      </section>
    </Card>
  )
}

export default RunSummary
