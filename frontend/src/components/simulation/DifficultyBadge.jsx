import { DIFFICULTY_LEVELS } from '../../config/simulation.js'

// Training difficulty: the label plus 1–3 filled bars, so it never relies on
// colour. Deliberately neutral/violet — difficulty is not attack severity.
function DifficultyBadge({ difficulty }) {
  return (
    <span className="inline-flex items-center gap-2 text-xs text-fg-muted">
      <span className="flex items-end gap-0.5" aria-hidden="true">
        {Array.from({ length: DIFFICULTY_LEVELS }, (_, index) => (
          <span
            key={index}
            className={`w-1 rounded-sm ${index < difficulty.level ? 'bg-accent' : 'bg-border'}`}
            style={{ height: `${6 + index * 3}px` }}
          />
        ))}
      </span>
      <span>
        <span className="sr-only">Training difficulty: </span>
        {difficulty.label}
      </span>
    </span>
  )
}

export default DifficultyBadge
