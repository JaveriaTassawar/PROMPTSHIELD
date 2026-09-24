// Horizontal meter for a classification confidence, shown as a whole percent.
// The number is always visible, so the meter never relies on colour alone.
// `percent` comes from toConfidencePercent(); pass null when the API gave none.
const FILL = { safe: 'bg-safe', danger: 'bg-danger', warning: 'bg-warning' }

function ConfidenceMeter({ percent, variant, label = 'Classification confidence' }) {
  if (percent === null) {
    return <p className="text-sm text-fg-muted">Confidence not available for this result.</p>
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-mono text-[11px] tracking-widest text-fg-subtle uppercase">{label}</span>
        <span className="font-mono text-2xl font-semibold tabular-nums text-fg">
          {percent}
          <span className="text-base text-fg-muted">%</span>
        </span>
      </div>
      <div
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        aria-valuetext={`${percent} percent`}
        className="h-2 overflow-hidden rounded-full bg-surface-raised"
      >
        <div
          className={`h-full origin-left rounded-full ${FILL[variant]}`}
          style={{
            transform: `scaleX(${percent / 100})`,
            animation: 'grow-x 0.7s var(--ease-snappy) 0.25s both',
          }}
        />
      </div>
    </div>
  )
}

export default ConfidenceMeter
