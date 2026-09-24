import Badge from '../Badge.jsx'
import DifficultyBadge from './DifficultyBadge.jsx'
import { CheckIcon } from '../icons.jsx'

const ACCENT_BAR = { danger: 'bg-danger', warning: 'bg-warning' }

// One selectable scenario. A real radio input inside a label: arrow keys move
// between cards, and the selection is announced. Selection is shown by the
// violet border, glow and tick — never colour alone.
function ScenarioCard({ scenario, name, checked, onSelect }) {
  return (
    <label className="group relative flex h-full cursor-pointer flex-col overflow-hidden rounded-card border border-border/80 bg-surface/70 p-5 transition duration-200 ease-snappy hover:-translate-y-0.5 hover:border-accent/40 has-checked:border-accent has-checked:bg-primary/10 has-checked:shadow-glow has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-accent">
      <input
        type="radio"
        name={name}
        value={scenario.id}
        checked={checked}
        onChange={() => onSelect(scenario.id)}
        className="sr-only"
      />
      <span className={`absolute inset-x-0 top-0 h-0.5 opacity-60 ${ACCENT_BAR[scenario.detection.variant]}`} aria-hidden="true" />

      <div className="flex items-center justify-between gap-3">
        <span className="font-mono text-[11px] tracking-widest text-fg-subtle">{scenario.code}</span>
        <span
          className="flex h-5 w-5 items-center justify-center rounded-full border border-border transition duration-200 ease-snappy group-has-checked:border-accent group-has-checked:bg-accent"
          aria-hidden="true"
        >
          <CheckIcon className="h-3 w-3 scale-50 text-canvas opacity-0 transition duration-200 ease-snappy group-has-checked:scale-100 group-has-checked:opacity-100" strokeWidth="3" />
        </span>
      </div>

      <span className="mt-3 text-base font-semibold text-fg">{scenario.title}</span>
      <span className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1">
        <Badge variant={scenario.detection.variant}>{scenario.detection.label}</Badge>
        <span className="font-mono text-xs text-fg-muted">{scenario.subtype}</span>
      </span>
      <span className="mt-3 text-sm text-fg-muted">{scenario.summary}</span>

      <span className="mt-auto flex items-center pt-4">
        <span className="w-full border-t border-border/60 pt-3">
          <DifficultyBadge difficulty={scenario.difficulty} />
        </span>
      </span>
    </label>
  )
}

export default ScenarioCard
