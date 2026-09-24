import Badge from '../Badge.jsx'
import DifficultyBadge from './DifficultyBadge.jsx'
import PageHeader from '../PageHeader.jsx'

// Scenario identity for the active simulation: code, title, attack class,
// sub-type, training difficulty, and the local-preview disclosure.
function SimulationHeader({ scenario, eyebrow = 'Simulation' }) {
  return (
    <div className="flex flex-col gap-3">
      <PageHeader eyebrow={`${eyebrow} · ${scenario.code}`} title={scenario.title}>
        <div className="flex flex-col gap-0.5 sm:items-end">
          <p className="font-mono text-[11px] tracking-widest text-fg-muted uppercase">
            Training scenario · <span className="text-accent">Local preview</span>
          </p>
          <p className="text-xs text-fg-subtle sm:text-right">Scripted locally until the simulation service is connected</p>
        </div>
      </PageHeader>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <Badge variant={scenario.detection.variant}>{scenario.detection.label}</Badge>
        <span className="font-mono text-xs text-fg-muted">{scenario.subtype}</span>
        <span className="h-3 w-px bg-border" aria-hidden="true" />
        <DifficultyBadge difficulty={scenario.difficulty} />
      </div>
    </div>
  )
}

export default SimulationHeader
