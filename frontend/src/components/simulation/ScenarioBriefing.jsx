import Badge from '../Badge.jsx'
import Button from '../Button.jsx'
import Card from '../Card.jsx'
import DifficultyBadge from './DifficultyBadge.jsx'
import { ArrowRightIcon } from '../icons.jsx'

// Security briefing for the selected scenario. Shows only catalog content and
// the shared taxonomy definition — no statistics, scores or telemetry.
function BriefingItem({ label, children }) {
  return (
    <div>
      <dt className="font-mono text-[11px] tracking-widest text-fg-subtle uppercase">{label}</dt>
      <dd className="mt-1.5 text-sm text-fg-muted">{children}</dd>
    </div>
  )
}

function ScenarioBriefing({ scenario, onStart, headingRef }) {
  return (
    <Card borderClassName="border-accent/30" className="animate-fade-up p-5 sm:p-6">
      <section aria-labelledby="briefing-heading">
        <p className="font-mono text-[11px] tracking-widest text-cyan/80 uppercase">Security briefing · {scenario.code}</p>
        <h2 id="briefing-heading" ref={headingRef} tabIndex={-1} className="mt-1.5 rounded text-xl font-semibold text-fg">
          {scenario.title}
        </h2>

        <dl className="mt-5 grid gap-5 md:grid-cols-2 md:gap-x-8">
          <BriefingItem label="What you’re practising">{scenario.summary}</BriefingItem>
          <BriefingItem label="Attack pattern">
            <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <Badge variant={scenario.detection.variant}>{scenario.detection.label}</Badge>
              <span className="font-medium text-fg">{scenario.subtype}</span>
            </span>
            {scenario.subtypeDefinition && <span className="mt-1.5 block">{scenario.subtypeDefinition}</span>}
          </BriefingItem>
          <BriefingItem label="Training objective">{scenario.objective}</BriefingItem>
          <BriefingItem label="Difficulty">
            <DifficultyBadge difficulty={scenario.difficulty} />
            <span className="mt-1.5 block text-xs text-fg-subtle">Training difficulty — not a measure of attack severity.</span>
          </BriefingItem>
        </dl>

        <div className="mt-6 flex flex-col gap-3 border-t border-border/70 pt-5 sm:flex-row sm:items-center sm:justify-end">
          <Button type="button" onClick={onStart} className="w-full sm:w-auto sm:min-w-48">
            Start Simulation
            <ArrowRightIcon className="h-4.5 w-4.5" />
          </Button>
        </div>
      </section>
    </Card>
  )
}

export default ScenarioBriefing
