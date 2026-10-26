// Accessible progress bar with its value always stated in text.
function ProgressBar({ label, value, max, valueText }) {
  const fraction = max ? value / max : 0

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-mono text-[11px] tracking-widest text-fg-subtle uppercase">{label}</span>
        <span className="font-mono text-xs tabular-nums text-fg-muted">{valueText}</span>
      </div>
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={value}
        aria-valuetext={valueText}
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

export default ProgressBar
