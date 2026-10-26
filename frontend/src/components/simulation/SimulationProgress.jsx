// Scenario progress: turns sent out of the script's total. Not a score.
function SimulationProgress({ sent, total }) {
  const text = sent === 0 ? `Not started · ${total} turns` : sent === total ? `Complete · ${total} of ${total} turns` : `Turn ${sent} of ${total}`
  const fraction = total ? sent / total : 0

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-mono text-[11px] tracking-widest text-fg-subtle uppercase">Scenario progress</span>
        <span className="font-mono text-xs tabular-nums text-fg-muted">{text}</span>
      </div>
      <div
        role="progressbar"
        aria-label="Scenario progress"
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={sent}
        aria-valuetext={text}
        className="h-1.5 overflow-hidden rounded-full bg-surface-raised"
      >
        <div
          className="h-full origin-left rounded-full bg-linear-to-r from-primary to-accent transition-transform duration-500 ease-snappy"
          style={{ transform: `scaleX(${fraction})` }}
        />
      </div>
    </div>
  )
}

export default SimulationProgress
