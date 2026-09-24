import Badge from '../Badge.jsx'
import { CheckIcon } from '../icons.jsx'

const ACCENT_BAR = { safe: 'bg-safe', danger: 'bg-danger', warning: 'bg-warning' }

// One tutorial module. The completion toggle is a real button with
// aria-pressed; completion is shown by text and icon, not colour alone.
function TutorialCard({ module, completed, onToggle }) {
  return (
    <article
      className={`relative flex h-full flex-col overflow-hidden rounded-card border bg-surface/70 p-5 transition-colors duration-200 ${
        completed ? 'border-accent/40' : 'border-border/80'
      }`}
      aria-labelledby={`module-${module.id}-title`}
    >
      <span className={`absolute inset-x-0 top-0 h-0.5 opacity-60 ${ACCENT_BAR[module.variant]}`} aria-hidden="true" />

      <div className="flex items-start justify-between gap-3">
        <Badge variant={module.variant}>{module.categoryLabel}</Badge>
        {completed && (
          <span className="flex items-center gap-1 font-mono text-[10px] tracking-widest text-accent uppercase">
            <CheckIcon className="h-3.5 w-3.5" strokeWidth="2.5" />
            Completed
          </span>
        )}
      </div>

      <h3 id={`module-${module.id}-title`} className="mt-3 text-base font-semibold text-fg">
        {module.title}
      </h3>
      <p className="mt-1.5 text-sm text-fg-muted">{module.summary}</p>

      <div className="mt-4 rounded-control border-l-2 border-cyan/70 bg-cyan/5 px-3 py-2">
        <p className="font-mono text-[10px] tracking-widest text-cyan/90 uppercase">{module.practice.label}</p>
        <p className="mt-0.5 text-sm text-fg">{module.practice.text}</p>
      </div>

      <div className="mt-auto pt-4">
        <button
          type="button"
          onClick={() => onToggle(module.id)}
          aria-pressed={completed}
          className={`flex w-full items-center justify-center gap-2 rounded-control border px-3 py-2 text-sm font-medium transition duration-150 ease-snappy ${
            completed
              ? 'border-accent/50 bg-primary/15 text-fg hover:bg-primary/25'
              : 'border-border bg-canvas/50 text-fg-muted hover:border-accent/50 hover:text-fg'
          }`}
        >
          <span
            aria-hidden="true"
            className={`flex h-4 w-4 items-center justify-center rounded border transition-colors ${
              completed ? 'border-accent bg-accent text-canvas' : 'border-fg-subtle'
            }`}
          >
            {completed && <CheckIcon className="h-3 w-3" strokeWidth="3" />}
          </span>
          Completed<span className="sr-only">: {module.title}</span>
        </button>
      </div>
    </article>
  )
}

export default TutorialCard
